/* GReport-Karte für Home-Assistant-Dashboards (custom:greport-card) – Version {{VERSION}}
 * Zeigt die GReport-Oberfläche direkt im Dashboard. Die Ingress-Adresse ist bei jeder Installation anders –
 * die Karte fragt sie beim Laden selbst bei Home Assistant ab und hält die Ingress-Sitzung gültig.
 * Optionen: height (z. B. "600px", Standard "auto" = so hoch wie der Inhalt), title (Überschrift, leer = keine).
 */
(() => {
  const de = () => ((document.documentElement.lang || navigator.language || "de").toLowerCase().startsWith("de"));
  const T = (d, e) => (de() ? d : e);

  class GReportCard extends HTMLElement {
    setConfig(config) {
      this._config = Object.assign({ height: "auto", title: "" }, config || {});
      if (this._frame) this._applyHeight();
      if (this._head) this._head.textContent = this._config.title || "";
    }

    set hass(hass) {
      this._hass = hass;
      if (!this._started) {
        this._started = true;
        this._start();
      }
    }

    getCardSize() { return 8; }
    getGridOptions() { return { columns: 12, min_columns: 6 }; }
    static getStubConfig() { return { height: "auto" }; }

    disconnectedCallback() {
      clearInterval(this._timer); this._timer = null;
      if (this._ro) this._ro.disconnect();
    }

    connectedCallback() {
      if (this._started && this._url && !this._timer) this._keepAlive();
    }

    _sv(endpoint, method = "get", data) {
      const msg = { type: "supervisor/api", endpoint, method };
      if (data) msg.data = data;
      return this._hass.callWS(msg);
    }

    _shell() {
      if (this._card) return;
      this._card = document.createElement("ha-card");
      this._card.style.overflow = "hidden";
      this._head = document.createElement("div");
      this._head.style.cssText = "padding:12px 16px 0;font-size:16px;font-weight:500";
      this._head.textContent = (this._config && this._config.title) || "";
      this._msg = document.createElement("div");
      this._msg.style.cssText = "padding:16px;color:var(--secondary-text-color)";
      this._card.append(this._head, this._msg);
      this.appendChild(this._card);
    }

    _say(text) { this._shell(); this._msg.textContent = text; this._msg.style.display = text ? "" : "none"; }

    async _session(check) {
      if (check && this._sess) {
        try { await this._sv("/ingress/validate_session", "post", { session: this._sess }); return; } catch (e) { /* neu holen */ }
      }
      const r = await this._sv("/ingress/session", "post");
      this._sess = r.session;
      document.cookie = `ingress_session=${r.session};path=/api/hassio_ingress/;SameSite=Strict${location.protocol === "https:" ? ";Secure" : ""}`;
    }

    _keepAlive() {
      clearInterval(this._timer);
      this._timer = setInterval(() => this._session(true).catch(() => {}), 60000);
    }

    async _start() {
      this._say(T("GReport wird geladen …", "Loading GReport …"));
      try {
        let addons;
        try { addons = await this._sv("/addons"); } catch (e) {
          throw new Error(T("Die GReport-Karte braucht einen Administrator-Benutzer.", "The GReport card needs an administrator user."));
        }
        const a = (addons.addons || []).find((x) => x.slug === "greport" || /_greport$/.test(x.slug));
        if (!a) throw new Error(T("GReport ist nicht installiert.", "GReport is not installed."));
        const info = await this._sv(`/addons/${a.slug}/info`);
        if (info.state !== "started") throw new Error(T("GReport läuft nicht – in Einstellungen → Apps starten.", "GReport is not running – start it under Settings → Apps."));
        if (!info.ingress_url) throw new Error(T("GReport hat keine Ingress-Adresse.", "GReport has no ingress address."));
        await this._session();
        this._keepAlive();
        this._url = info.ingress_url;
        this._frame = document.createElement("iframe");
        this._frame.title = "GReport";
        this._frame.style.cssText = "display:block;width:100%;border:0;background:transparent";
        this._frame.src = this._url;
        this._frame.addEventListener("load", () => this._watch());
        this._applyHeight();
        this._say("");
        this._card.appendChild(this._frame);
      } catch (e) {
        this._say(e && e.message ? e.message : String(e));
      }
    }

    _applyHeight() {
      const h = String((this._config && this._config.height) || "auto");
      this._auto = h === "auto";
      if (!this._auto) this._frame.style.height = /^\d+$/.test(h) ? h + "px" : h;
      else if (!this._frame.style.height) this._frame.style.height = "640px";
    }

    _watch() {
      if (this._ro) this._ro.disconnect();
      if (!this._auto) return;
      let doc;
      try { doc = this._frame.contentDocument; } catch (e) { return; }
      if (!doc || !doc.body) return;
      const fit = () => {
        const h = Math.max(doc.body.scrollHeight, doc.documentElement.scrollHeight);
        if (h && Math.abs(h - this._frame.offsetHeight) > 2) this._frame.style.height = h + "px";
      };
      this._ro = new ResizeObserver(fit);
      this._ro.observe(doc.body);
      fit();
    }
  }

  if (!customElements.get("greport-card")) customElements.define("greport-card", GReportCard);
  window.customCards = window.customCards || [];
  if (!window.customCards.some((c) => c.type === "greport-card")) {
    window.customCards.push({
      type: "greport-card",
      name: "GReport",
      description: T("Die GReport-Oberfläche im Dashboard: Notiz jetzt, Schnellwahl, Liste.", "The GReport interface on your dashboard: note now, quick select, list."),
      preview: false,
      documentationURL: "https://www.gsimulations.de/greport/",
    });
  }
})();
