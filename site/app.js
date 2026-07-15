/* Банкарски имот — client logic. No framework: fast on a phone, easy to host. */
(function () {
  "use strict";

  var state = { all: [], bank: null, type: null, onlyNew: false, q: "" };

  var grid = document.getElementById("grid");
  var searchEl = document.getElementById("search");
  var banksEl = document.getElementById("banks");
  var typesEl = document.getElementById("types");
  var resultMeta = document.getElementById("resultmeta");

  var PIN = '<svg width="12" height="12" viewBox="0 0 24 24" fill="currentColor"><path d="M12 2C8.1 2 5 5.1 5 9c0 5.2 7 13 7 13s7-7.8 7-13c0-3.9-3.1-7-7-7zm0 9.5A2.5 2.5 0 1112 6.5a2.5 2.5 0 010 5z"/></svg>';
  var ARROW = '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"><path d="M5 12h14M13 6l6 6-6 6"/></svg>';

  function esc(s) {
    return String(s == null ? "" : s).replace(/[&<>"']/g, function (m) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[m];
    });
  }

  function fmtArea(a) {
    if (!a) return null;
    return (Math.round(a * 10) / 10).toLocaleString("mk-MK") + " м²";
  }
  function fmtPrice(p, cur) {
    if (!p) return null;
    return p.toLocaleString("mk-MK") + " " + (cur === "MKD" ? "ден" : "€");
  }

  function load() {
    // network-first so weekly updates always show; SW serves the cache offline
    fetch("./data/listings.json?v=" + Date.now(), { cache: "no-store" })
      .then(function (r) { if (!r.ok) throw new Error(r.status); return r.json(); })
      .then(init)
      .catch(function () {
        // offline: try whatever the service worker cached
        fetch("./data/listings.json").then(function (r) { return r.json(); }).then(init)
          .catch(function () {
            grid.innerHTML = '<div class="empty"><b>Нема податоци</b>Проверете ја врската и обидете се повторно.</div>';
          });
      });
  }

  function init(data) {
    state.all = data.listings || [];
    document.getElementById("s-count").textContent = data.count || state.all.length;
    document.getElementById("s-banks").textContent = Object.keys(data.banks || {}).length;
    document.getElementById("s-new").textContent = data.new_count || 0;
    var d = (data.generated_at || "").slice(0, 10);
    document.getElementById("s-date").textContent = d ? "ажур. " + d : "";
    document.getElementById("foot-updated").textContent =
      d ? "Последно ажурирање: " + d : "";
    buildFilters(data.banks || {});
    render();
  }

  function buildFilters(banks) {
    // bank chips, ordered by count desc
    var order = Object.keys(banks).sort(function (a, b) { return banks[b] - banks[a]; });
    banksEl.innerHTML = "";
    banksEl.appendChild(chip("Сите банки", null, "bank", true));
    order.forEach(function (b) {
      banksEl.appendChild(chip(b + " · " + banks[b], b, "bank", false));
    });

    var types = {};
    state.all.forEach(function (x) { if (x.type) types[x.type] = (types[x.type] || 0) + 1; });
    var tOrder = Object.keys(types).sort(function (a, b) { return types[b] - types[a]; });
    typesEl.innerHTML = "";
    var newChip = chip("Само нови", "__new__", "new", false);
    newChip.classList.add("stamp");
    typesEl.appendChild(newChip);
    typesEl.appendChild(chip("Сите типови", null, "type", true));
    tOrder.forEach(function (t) { typesEl.appendChild(chip(t, t, "type", false)); });
  }

  function chip(label, value, group, pressed) {
    var b = document.createElement("button");
    b.className = "chip";
    b.textContent = label;
    b.setAttribute("aria-pressed", pressed ? "true" : "false");
    b.addEventListener("click", function () {
      if (group === "new") {
        state.onlyNew = !state.onlyNew;
        b.setAttribute("aria-pressed", state.onlyNew ? "true" : "false");
      } else {
        state[group] = value;
        var row = group === "bank" ? banksEl : typesEl;
        row.querySelectorAll(".chip:not(.stamp)").forEach(function (c) {
          c.setAttribute("aria-pressed", "false");
        });
        b.setAttribute("aria-pressed", "true");
      }
      render();
    });
    return b;
  }

  function match(x) {
    if (state.bank && x.bank !== state.bank) return false;
    if (state.type && x.type !== state.type) return false;
    if (state.onlyNew && !x.is_new) return false;
    if (state.q) {
      var hay = (x.title + " " + (x.location || "") + " " + (x.type || "") + " " + x.bank).toLowerCase();
      if (hay.indexOf(state.q) === -1) return false;
    }
    return true;
  }

  function render() {
    var rows = state.all.filter(match);
    resultMeta.textContent = rows.length + " од " + state.all.length + " огласи";
    if (!rows.length) {
      grid.innerHTML = '<div class="empty"><b>Нема резултати</b>Пробајте друг збор или отстранете некои филтри.</div>';
      return;
    }
    grid.innerHTML = rows.map(card).join("");
  }

  function card(x) {
    var data = [];
    var area = fmtArea(x.area_m2);
    if (area) data.push('<span class="datum"><span class="k">површина</span> ' + esc(area) + "</span>");
    var price = fmtPrice(x.price, x.currency);
    data.push('<span class="datum"><span class="k">цена</span> ' + (price ? esc(price) : "по договор") + "</span>");
    if (x.deed) data.push('<span class="datum"><span class="k">ИЛ</span> ' + esc(x.deed) + "</span>");

    var href = x.pdf_url || x.source_url;
    return (
      '<article class="card' + (x.is_new ? " is-new" : "") + '">' +
      (x.is_new ? '<div class="newstamp">НОВО</div>' : "") +
      '<span class="banktag">' + esc(x.bank) + "</span>" +
      "<h2>" + esc(x.title) + "</h2>" +
      (x.location ? '<div class="loc">' + PIN + "<span>" + esc(x.location) + "</span></div>" : "") +
      '<div class="data">' + data.join("") + "</div>" +
      (href ? '<a class="open" href="' + esc(href) + '" target="_blank" rel="noopener">Отвори оглас ' + ARROW + "</a>" : "") +
      "</article>"
    );
  }

  var t;
  searchEl.addEventListener("input", function () {
    clearTimeout(t);
    t = setTimeout(function () { state.q = searchEl.value.trim().toLowerCase(); render(); }, 120);
  });

  load();

  if ("serviceWorker" in navigator) {
    window.addEventListener("load", function () {
      navigator.serviceWorker.register("./sw.js").catch(function () {});
    });
  }
})();
