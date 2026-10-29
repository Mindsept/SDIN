"""Repository fixtures exercise navigation regressions without network or AI."""
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from check_ai_docs import Checker, git_files  # noqa: E402

SCRIPT = Path(__file__).resolve().parents[1] / 'check_ai_docs.py'


class DocumentationTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name).resolve()
        self.put('AGENTS.md', '[Use the skill](skills/demo/SKILL.md)\n')
        self.put('skills/demo/SKILL.md',
                 '---\nname: demo\ndescription: A useful skill\n---\n# Demo\n')

    def put(self, name, text):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)

    def check(self):
        files = [p.relative_to(self.root).as_posix() for p in self.root.rglob('*')
                 if p.is_file() or p.is_symlink()]
        checker = Checker(self.root, files)
        checker.run()
        return checker

    def assert_clean(self):
        checker = self.check()
        self.assertEqual([], checker.issues, '\n'.join(map(str, checker.issues)))
        return checker

    def assert_error(self, code, part):
        issues = self.check().issues
        self.assertTrue(any(i.code == code and part in i.detail for i in issues),
                        '\n'.join(map(str, issues)))

    def test_current_contract_does_not_require_optional_agent_metadata(self):
        self.assert_clean()

    def test_root_skill_and_optional_metadata_are_discovered(self):
        self.put('AGENTS.md', '[Main](SKILL.md) [Demo](skills/demo/SKILL.md)\n')
        self.put('SKILL.md', '---\nname: root-skill\ndescription: Root\n---\n')
        self.put('agents/openai.yaml', 'interface:\n  default_prompt: "Use $root-skill."\n')
        self.assert_clean()

    def test_indirect_routing_directory_readme_and_cycles_are_valid(self):
        self.put('AGENTS.md', '[Route](guide/)\n')
        self.put('guide/README.md', '[Skill](../skills/demo/SKILL.md) [Back](../AGENTS.md)\n')
        self.assert_clean()

    def test_new_skill_must_be_reachable_without_a_fixed_catalog_size(self):
        self.put('skills/new/SKILL.md', '---\nname: new\ndescription: Another\n---\n')
        self.assert_error('ROUTING', 'not reachable')
        self.put('skills/demo/SKILL.md', '---\nname: demo\ndescription: Example\n---\n'
                 '[Next](../new/SKILL.md)\n')
        self.assert_clean()

    def test_image_of_skill_is_not_a_navigation_route(self):
        self.put('AGENTS.md', '![Not a link](skills/demo/SKILL.md)\n')
        self.assert_error('ROUTING', 'not reachable')

    def test_missing_entry_point_cannot_pass(self):
        (self.root / 'AGENTS.md').unlink()
        self.assert_error('ROUTING', 'entry point')

    def test_renamed_reference_fails_with_source_location(self):
        self.put('guide.md', '# Guide\n\n[Rules](missing.md)\n')
        issues = self.check().issues
        self.assertTrue(any(i.path == 'guide.md' and i.line == 3 and 'missing.md' in i.detail
                            for i in issues))

    def test_text_changes_and_fictitious_code_paths_are_not_links(self):
        self.put('guide.md', '# Explanation\n\nChanged prose and `path/to/future.md`.\n'
                 '```md\n[Example](future.md)\n```\n'
                 '    [Indented example](not-created.md)\n'
                 '`[Inline example](also-not-created.md)`\n'
                 '<!-- <a href="missing.md">Comment</a> -->\n')
        self.assert_clean()

    def test_reference_links_tables_encoded_paths_and_titles(self):
        self.put('a file.md', '# Résumé\n')
        self.put('guide.md', '| Reference |\n|---|\n| [Read][id] |\n\n'
                 '[id]: <a file.md#résumé> "Title"\n'
                 '[Other](a%20file.md?raw=1#r%C3%A9sum%C3%A9)\n')
        self.assert_clean()

    def test_html_links_images_and_explicit_ids(self):
        self.put('guide.md', '<span id="custom"></span>\n\n'
                 '<a href="guide.md#custom">Read</a>\n'
                 '<img src="asset.svg"/>\n')
        self.put('asset.svg', '<svg/>')
        self.assert_clean()
        self.put('guide.md', '<a href="missing.md">Read</a>\n')
        self.assert_error('LINK', 'missing.md')

    def test_unicode_duplicate_and_formatted_heading_anchors(self):
        self.put('guide.md', '# Résumé : `code`\n# Résumé : code\n'
                 'Setext title\n============\n'
                 '[One](#résumé--code) [Two](#résumé--code-1) [Three](#setext-title)\n')
        self.assert_clean()

    def test_missing_anchor_is_an_error_but_non_markdown_fragments_are_explicit(self):
        self.put('guide.md', '# Existing\n[Missing](#absent)\n')
        self.assert_error('LINK', 'anchor #absent')
        self.put('guide.md', '[Image section](asset.svg#part)\n')
        self.put('asset.svg', '<svg/>')
        checker = self.assert_clean()
        self.assertEqual(1, checker.unchecked_fragments)

    def test_external_urls_are_not_fetched(self):
        self.put('guide.md', '[Offline](https://not-resolved.invalid/a#missing)\n'
                 '[Protocol relative](//not-resolved.invalid/a)\n'
                 '<https://not-resolved.invalid/>\n')
        self.assert_clean()

    def test_target_case_must_match_git_inventory_even_on_macos(self):
        self.put('guide.md', '[Wrong case](agents.md)\n')
        self.assert_error('LINK', 'absent')

    def test_link_cannot_leave_repository_or_read_an_external_symlink(self):
        self.put('guide.md', '[Outside](../outside.md)\n')
        self.assert_error('LINK', 'leaves the repository')
        self.put('guide.md', '[Outside](outside.txt)\n')
        (self.root / 'outside.txt').symlink_to(self.root.parent / 'not-to-be-read')
        self.assert_error('LINK', 'symlink leaves')

    def test_markdown_symlink_outside_repository_is_not_read(self):
        (self.root / 'outside.md').symlink_to(self.root.parent / 'not-to-be-read')
        self.assert_error('READ', 'leaves the repository')

    def test_missing_or_unclosed_skill_frontmatter_fails(self):
        for text in ('# Demo\n', '---\nname: demo\n'):
            with self.subTest(text=text):
                self.put('skills/demo/SKILL.md', text)
                self.assert_error('METADATA', 'closed YAML')

    def test_required_metadata_types_and_duplicate_names(self):
        self.put('skills/demo/SKILL.md', '---\nname: true\ndescription: []\n---\n')
        self.assert_error('METADATA', 'nonempty string')
        self.put('skills/demo/SKILL.md', '---\nname: DEMO\ndescription: Fine\n---\n')
        self.put('skills/new/SKILL.md', '---\nname: demo\ndescription: Fine\n---\n')
        self.assert_error('METADATA', 'duplicate skill name')

    def test_folded_yaml_and_name_different_from_folder_are_valid(self):
        self.put('skills/demo/SKILL.md', '---\nname: another-name\ndescription: >-\n'
                 '  A valid folded\n  description.\n---\n')
        self.assert_clean()

    def test_duplicate_yaml_keys_and_unsafe_tags_are_rejected(self):
        for header in ('name: demo\nname: other\ndescription: Fine',
                       'name: demo\ndescription: !!python/object/apply:os.system [false]'):
            with self.subTest(header=header):
                self.put('skills/demo/SKILL.md', '---\n' + header + '\n---\n')
                self.assertTrue(any(i.code == 'METADATA' for i in self.check().issues))

    def test_optional_agent_metadata_accepts_prose_and_matching_invocation(self):
        for prompt in ('Use the relevant documentation.', 'Use $demo for this change.'):
            with self.subTest(prompt=prompt):
                self.put('skills/demo/agents/openai.yaml',
                         f'interface:\n  default_prompt: "{prompt}"\n')
                self.assert_clean()

    def test_optional_agent_metadata_rejects_mismatch_or_invalid_types(self):
        for text in ('interface: []\n', 'interface:\n  default_prompt: 12\n',
                     'interface:\n  default_prompt: "Use $missing."\n'):
            with self.subTest(text=text):
                self.put('skills/demo/agents/openai.yaml', text)
                self.assertTrue(any(i.code == 'METADATA' for i in self.check().issues))

    def test_metadata_for_another_known_skill_is_also_a_mismatch(self):
        self.put('skills/new/SKILL.md', '---\nname: new\ndescription: Another\n---\n')
        self.put('skills/demo/agents/openai.yaml',
                 'interface:\n  default_prompt: "Use $new."\n')
        self.assert_error('METADATA', 'different skill')

    def test_git_inventory_ignores_generated_docs_but_includes_new_work(self):
        subprocess.run(['git', 'init', '-q', str(self.root)], check=True)
        self.put('.gitignore', 'generated/\n')
        self.put('generated/broken.md', '[Missing](never-created.md)\n')
        subprocess.run(['git', '-C', str(self.root), 'add', 'AGENTS.md'], check=True)
        files = git_files(self.root)
        self.assertNotIn('generated/broken.md', files)
        self.assertIn('skills/demo/SKILL.md', files)
        checker = Checker(self.root, files)
        checker.run()
        self.assertEqual([], checker.issues)

    def test_cli_statuses_are_meaningful_and_do_not_modify_sources(self):
        subprocess.run(['git', 'init', '-q', str(self.root)], check=True)
        command = [sys.executable, '-B', str(SCRIPT), '--repo', str(self.root)]
        before = (self.root / 'AGENTS.md').read_bytes()
        result = subprocess.run(command, capture_output=True, text=True)
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        self.assertEqual(before, (self.root / 'AGENTS.md').read_bytes())
        self.put('broken.md', '[Missing](gone.md)\n')
        result = subprocess.run(command, capture_output=True, text=True)
        self.assertEqual(1, result.returncode)
        self.assertIn('broken.md:1: error [LINK]', result.stdout)
        result = subprocess.run(command[:-1] + [str(self.root / 'missing')],
                                capture_output=True, text=True)
        self.assertEqual(2, result.returncode)


if __name__ == '__main__':
    unittest.main()
