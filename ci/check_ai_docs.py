#!/usr/bin/env python3
"""Check local documentation navigation, not AI decisions or live services."""
import argparse
from collections import deque
from dataclasses import dataclass
from html.parser import HTMLParser
from pathlib import Path
import posixpath
import re
import subprocess
import sys
import unicodedata
from urllib.parse import unquote, urlsplit

try:
    from markdown_it import MarkdownIt
    import yaml
except ImportError:
    print('Install CI parsers first: python3 -m pip install -r ci/requirements.txt',
          file=sys.stderr)
    sys.exit(2)


class UniqueSafeLoader(yaml.SafeLoader):
    """Safe YAML with ambiguous duplicate keys rejected."""


def unique_mapping(loader, node):
    loader.flatten_mapping(node)
    result = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=True)
        if not isinstance(key, (str, int, float, bool, type(None))):
            raise yaml.constructor.ConstructorError(
                None, None, 'metadata keys must be scalar', key_node.start_mark)
        if key in result:
            raise yaml.constructor.ConstructorError(
                None, None, f'duplicate key {key!r}', key_node.start_mark)
        result[key] = loader.construct_object(value_node, deep=True)
    return result


UniqueSafeLoader.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,
                                 unique_mapping)


@dataclass(frozen=True)
class Issue:
    path: str
    line: int
    code: str
    detail: str

    def __str__(self):
        return f'{self.path}:{self.line}: error [{self.code}] {self.detail}'


@dataclass(frozen=True)
class Link:
    target: str
    line: int
    navigation: bool = True


class HTMLReferences(HTMLParser):
    def __init__(self, line):
        super().__init__(convert_charrefs=True)
        self.line = line
        self.links = []
        self.anchors = set()

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        for key in ('id', 'name' if tag == 'a' else 'id'):
            if attrs.get(key):
                self.anchors.add(attrs[key])
        key = 'href' if tag == 'a' else 'src' if tag in ('img', 'source') else None
        if key and attrs.get(key):
            self.links.append(Link(attrs[key], self.line + self.getpos()[0] - 1,
                                   tag == 'a'))

    handle_startendtag = handle_starttag


def frontmatter(text):
    """Return YAML and its line count; fenced examples are not metadata."""
    lines = text.splitlines(keepends=True)
    if not lines or lines[0].strip() != '---':
        return None, 0
    for index in range(1, len(lines)):
        if lines[index].strip() == '---':
            return ''.join(lines[1:index]), index + 1
    return None, 0


def slug(text):
    # Supported GitHub-style heading IDs: Unicode text, punctuation removed,
    # literal spaces replaced by hyphens; repeated IDs get numeric suffixes.
    return ''.join(c for c in text.lower()
                   if c in '-_ ' or unicodedata.category(c)[0] not in 'PSC').replace(' ', '-')


def markdown(text):
    _, offset = frontmatter(text)
    lines = text.splitlines(keepends=True)
    body = '\n' * offset + ''.join(lines[offset:])
    parser = MarkdownIt('commonmark', {'html': True}).enable('table')
    tokens = parser.parse(body)
    links, anchors, occupied = [], set(), set()

    def html_refs(token, line):
        reader = HTMLReferences(line)
        reader.feed(token.content)
        links.extend(reader.links)
        anchors.update(reader.anchors)

    for index, token in enumerate(tokens):
        line = token.map[0] + 1 if token.map else 1
        if token.type == 'heading_open' and index + 1 < len(tokens):
            children = tokens[index + 1].children or []
            title = ''.join(child.content for child in children
                            if child.type in ('text', 'code_inline', 'image'))
            base = slug(title)
            anchor, suffix = base, 0
            while anchor in occupied:
                suffix += 1
                anchor = f'{base}-{suffix}'
            occupied.add(anchor)
            anchors.add(anchor)
        if token.type == 'html_block':
            html_refs(token, line)
        if token.type != 'inline':
            continue
        for child in token.children or []:
            if child.type == 'link_open':
                links.append(Link(child.attrGet('href'), line))
            elif child.type == 'image':
                links.append(Link(child.attrGet('src'), line, False))
            elif child.type == 'html_inline':
                html_refs(child, line)
    return links, anchors


class Checker:
    def __init__(self, root, files):
        self.root = Path(root).resolve()
        self.files = set(files)
        self.issues = []
        self.documents = {}
        self.graph = {}
        self.link_count = 0
        self.unchecked_fragments = 0

    def issue(self, path, line, code, detail):
        self.issues.append(Issue(path, line, code, detail))

    def read(self, path):
        full = self.root / path
        try:
            if not full.resolve().is_relative_to(self.root):
                raise ValueError('path or symlink leaves the repository')
            return full.read_text(encoding='utf-8-sig')
        except (OSError, UnicodeError, ValueError, RuntimeError) as exc:
            self.issue(path, 1, 'READ', str(exc))
            return None

    def load_yaml(self, path, text, offset=0):
        try:
            data = yaml.load(text, Loader=UniqueSafeLoader)
            if not isinstance(data, dict):
                raise ValueError('expected a YAML mapping')
            return data
        except (yaml.YAMLError, ValueError) as exc:
            mark = getattr(exc, 'problem_mark', None)
            line = offset + mark.line + 1 if mark else offset + 1
            self.issue(path, line, 'METADATA', str(exc).splitlines()[0])
            return None

    def check_link(self, source, link):
        self.link_count += 1
        try:
            url = urlsplit(link.target)
            if url.scheme or url.netloc:
                return  # No network requests; external URLs are outside scope.
            raw = unquote(url.path)
            if '\x00' in raw or '\\' in raw:
                raise ValueError('invalid portable local path')
            target = (posixpath.normpath(posixpath.join(posixpath.dirname(source), raw))
                      if raw else source)
            if raw.startswith('/'):
                target = posixpath.normpath(raw.lstrip('/'))
            if target == '..' or target.startswith('../'):
                raise ValueError('local link leaves the repository')
            full = self.root / target
            if not full.resolve().is_relative_to(self.root):
                raise ValueError('target symlink leaves the repository')
            prefix = target.rstrip('/') + '/' if target != '.' else ''
            if target not in self.files:
                if not any(name.startswith(prefix) for name in self.files):
                    raise ValueError('target is absent or not in the Git file inventory')
                target = next((prefix + name for name in ('README.md', 'readme.md', 'Readme.md')
                               if prefix + name in self.documents), None)
                if target is None:
                    if url.fragment:
                        self.unchecked_fragments += 1
                    return
            if not full.exists():
                raise ValueError('target is missing from the working tree')
            fragment = unquote(url.fragment)
            if fragment and target in self.documents:
                if fragment not in self.documents[target][1]:
                    raise ValueError(f'Markdown anchor #{fragment} does not exist')
            elif fragment:
                self.unchecked_fragments += 1
            if link.navigation and target in self.documents:
                self.graph[source].add(target)
        except (OSError, ValueError, RuntimeError) as exc:
            self.issue(source, link.line, 'LINK', f'{link.target!r}: {exc}')

    def check_skills(self):
        names = {}
        skills = sorted(path for path in self.files if Path(path).name == 'SKILL.md')
        for path in skills:
            text = self.read(path)
            if text is None:
                continue
            header, _ = frontmatter(text)
            if header is None:
                self.issue(path, 1, 'METADATA', 'SKILL.md requires closed YAML front matter')
                continue
            data = self.load_yaml(path, header, 1)
            if data is None:
                continue
            for field in ('name', 'description'):
                if not isinstance(data.get(field), str) or not data[field].strip():
                    self.issue(path, 2, 'METADATA', f'{field} must be a nonempty string')
            name = data.get('name')
            if isinstance(name, str) and name.strip():
                key = name.strip().casefold()
                if key in names:
                    self.issue(path, 2, 'METADATA', f'duplicate skill name; also in {names[key]}')
                names[key] = path

        known = set(names)
        for path in sorted(p for p in self.files
                           if Path(p).parts[-2:] == ('agents', 'openai.yaml')):
            skill = str(Path(path).parent.parent / 'SKILL.md')
            text = self.read(path)
            if skill not in skills:
                self.issue(path, 1, 'METADATA', 'agent metadata has no sibling skill')
            if text is None:
                continue
            data = self.load_yaml(path, text)
            if data is None:
                continue
            interface = data.get('interface', {})
            if not isinstance(interface, dict):
                self.issue(path, 1, 'METADATA', 'interface must be a mapping when present')
                continue
            for field in ('display_name', 'short_description', 'default_prompt'):
                if field in interface and (not isinstance(interface[field], str)
                                           or not interface[field].strip()):
                    self.issue(path, 1, 'METADATA', f'interface.{field} must be a nonempty string')
            prompt = interface.get('default_prompt')
            if isinstance(prompt, str):
                referenced = {s.casefold() for s in re.findall(r'\$([\w-]+)', prompt)}
                own = {name for name, filename in names.items() if filename == skill}
                if referenced - known or (referenced and not referenced.intersection(own)):
                    self.issue(path, 1, 'METADATA', 'default_prompt names an unknown or different skill')

        if 'AGENTS.md' not in self.documents:
            self.issue('AGENTS.md', 1, 'ROUTING', 'a readable root entry point is required')
            return skills
        seen, queue = set(), deque(['AGENTS.md'])
        while queue:
            path = queue.popleft()
            if path not in seen:
                seen.add(path)
                queue.extend(self.graph.get(path, ()))
        for path in skills:
            if path not in seen:
                self.issue(path, 1, 'ROUTING', 'not reachable by documentation links from AGENTS.md')
        return skills

    def run(self):
        for path in sorted(p for p in self.files if p.lower().endswith('.md')):
            text = self.read(path)
            if text is not None:
                self.documents[path] = markdown(text)
                self.graph[path] = set()
        for path, (links, _) in self.documents.items():
            for link in links:
                self.check_link(path, link)
        skills = self.check_skills()
        return skills


def git_files(root):
    result = subprocess.run(['git', '-C', str(root), 'ls-files', '--cached', '--others',
                             '--exclude-standard', '-z'], capture_output=True, check=True)
    return [p for p in result.stdout.decode('utf-8').split('\0') if p]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo', type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    try:
        root = args.repo.resolve(strict=True)
        checker = Checker(root, git_files(root))
        skills = checker.run()
    except (OSError, UnicodeError, subprocess.CalledProcessError) as exc:
        print(f'Cannot inspect repository: {exc}', file=sys.stderr)
        return 2
    for issue in sorted(set(checker.issues), key=lambda i: (i.path, i.line, i.code, i.detail)):
        print(issue)
    print(f'AI docs: {len(checker.documents)} Markdown files, {len(skills)} skills, '
          f'{checker.link_count} links, {len(checker.issues)} errors.')
    if checker.unchecked_fragments:
        print(f'Not verified: {checker.unchecked_fragments} fragments on non-Markdown targets.')
    print('External URLs, bare paths in prose/examples, AI decisions and live services are not checked.')
    return 1 if checker.issues else 0


if __name__ == '__main__':
    sys.exit(main())
