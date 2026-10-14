// Exemple navigateur à adapter : ni installation du tracker ni déduplication.
const routes = Object.freeze({
  cart_saved: "/cart",
  checkout_started: "/checkout",
  order_created: "/checkout/success",
});

export function trackBusinessEvent({ tracker, app, event, channel = "web" }) {
  if (typeof app !== "string" || !/^[a-z][a-z0-9-]*$/.test(app)) return;
  if (typeof event !== "string" || !Object.hasOwn(routes, event)) return;
  if (!["web", "mobile_web"].includes(channel)) return;
  const name = `${app}.${event}`;
  if (name.length > 50) return;

  try {
    if (typeof tracker?.track !== "function") return;
    const result = tracker.track((defaults) => ({
      ...defaults,
      name,
      url: routes[event],
      title: routes[event],
      referrer: "",
      data: { channel },
    }));
    // Une promesse rejetée ne remonte pas dans le parcours métier.
    void Promise.resolve(result).catch(() => {});
  } catch {
    // La collecte reste best-effort : pas de reprise automatique.
  }
}
