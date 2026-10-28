(function () {
  "use strict";
  var $ = function (s, r) { return (r || document).querySelector(s); };
  var $$ = function (s, r) { return Array.prototype.slice.call((r || document).querySelectorAll(s)); };
  var money = function (n) { return "$" + Math.round(n).toLocaleString("en-US"); };
  var reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  /* ---------- Home: rotating scene, live "how many fit" ---------- */
  var plan = $("#plan");
  if (plan) {
    var imgs = $$("#backdrop img"), cur = 0;
    function show(i) { imgs[cur].classList.remove("on"); cur = i; imgs[cur].classList.add("on"); }
    if (!reduce && imgs.length > 1) setInterval(function () { show((cur + 1) % imgs.length); }, 6500);

    var data = JSON.parse($("#dest-data").textContent);
    var origin = $("#origin"), budget = $("#budget"), range = $("#budget-r"), nights = $("#nights"), live = $("#live");

    function clamp(v, lo, hi, d) { v = parseInt(v, 10); return isNaN(v) ? d : Math.max(lo, Math.min(hi, v)); }
    function update() {
      var b = clamp(budget.value, 100, 20000, 1500), n = clamp(nights.value, 1, 30, 4);
      var o = origin.value.toUpperCase().replace(/[^A-Z]/g, "");
      var picked = $$('input[name="vibe"]:checked', plan).map(function (c) { return c.value; });
      var pool = data.filter(function (d) {
        return d.airport !== o && (!picked.length || picked.some(function (v) { return d.vibes.indexOf(v) > -1; }));
      });
      var fit = pool.filter(function (d) { return d.total1 + d.hotel * n <= b; });
      live.innerHTML = fit.length
        ? "<b>" + fit.length + "</b> of " + pool.length + " destinations fit " + money(b) + " for " + n + " night" + (n === 1 ? "" : "s") + "."
        : "No destination fits that yet. Try more budget or fewer nights.";
      if (fit.length && !reduce) {
        var cheapest = fit.reduce(function (a, d) { return d.total1 + d.hotel * n < a.total1 + a.hotel * n ? d : a; });
        var idx = imgs.findIndex(function (im) { return im.dataset.scene === cheapest.slug; });
        if (idx > -1 && idx !== cur) show(idx);
      }
    }
    budget.addEventListener("input", function () { range.value = Math.min(budget.value, 6000); update(); });
    range.addEventListener("input", function () { budget.value = range.value; update(); });
    nights.addEventListener("input", update);
    origin.addEventListener("input", function () { origin.value = origin.value.replace(/[^a-zA-Z]/g, "").toUpperCase(); update(); });
    $$("[data-step]", plan).forEach(function (b) {
      b.addEventListener("click", function () { nights.value = clamp(+nights.value + +b.dataset.step, 1, 30, 4); update(); });
    });
    $$('input[name="vibe"]', plan).forEach(function (c) { c.addEventListener("change", update); });
    plan.addEventListener("submit", function (e) {
      var ok = /^[A-Za-z]{3}$/.test(origin.value);
      origin.closest(".field").classList.toggle("invalid", !ok);
      if (!ok) { e.preventDefault(); origin.setCustomValidity("Enter a 3-letter airport code, like SEA."); origin.reportValidity(); }
      else origin.setCustomValidity("");
    });
    origin.addEventListener("input", function () { origin.setCustomValidity(""); });
    update();
  }

  /* ---------- Results: filter, sort, compare ---------- */
  var grid = $("#grid");
  if (grid) {
    var cards = $$(".card", grid), sort = $("#sort"), over = $("#over"), empty = $("#empty");
    var vibeBoxes = $$("#toolbar .chips input");
    function apply() {
      var picked = vibeBoxes.filter(function (c) { return c.checked; }).map(function (c) { return c.value; });
      var by = sort.value;
      cards.sort(function (a, b) {
        if (by === "name") return a.dataset.name.localeCompare(b.dataset.name);
        if (by === "left") return b.dataset.left - a.dataset.left;
        return (b.dataset.fits - a.dataset.fits) || (a.dataset.total - b.dataset.total);
      });
      var shown = 0;
      cards.forEach(function (c) {
        grid.appendChild(c);
        var vs = c.dataset.vibes.split(",");
        var vibeOk = !picked.length || picked.some(function (v) { return vs.indexOf(v) > -1; });
        var fitOk = over.checked || c.dataset.fits === "1";
        c.hidden = !(vibeOk && fitOk);
        if (!c.hidden) shown++;
      });
      empty.hidden = shown > 0;
      var sf = $("#sum-fit"), st = $("#sum-total");
      if (sf && st) { st.textContent = shown; sf.textContent = cards.filter(function (c) { return !c.hidden && c.dataset.fits === "1"; }).length; }
    }
    [sort, over].concat(vibeBoxes).forEach(function (el) { el.addEventListener("change", apply); });
    apply();

    var tray = $("#tray"), dlg = $("#cmp-dialog"), picked = [];
    function renderTray() {
      tray.hidden = picked.length === 0;
      $("#tray-n").textContent = picked.length + " selected" + (picked.length < 2 ? " (pick 2 or 3)" : "");
      $("#tray-go").disabled = picked.length < 2;
      $("#tray-go").style.opacity = picked.length < 2 ? .5 : 1;
    }
    $$(".cmp-box", grid).forEach(function (b) {
      b.addEventListener("change", function () {
        if (b.checked) {
          if (picked.length >= 3) { b.checked = false; $("#tray-n").textContent = "3 is the max. Uncheck one first."; return; }
          picked.push(b.value);
        } else picked = picked.filter(function (s) { return s !== b.value; });
        renderTray();
      });
    });
    $("#tray-clear").addEventListener("click", function () { picked = []; $$(".cmp-box").forEach(function (b) { b.checked = false; }); renderTray(); });
    $("#tray-go").addEventListener("click", function () {
      if (picked.length < 2) return;
      var rows = picked.map(function (s) { return $('.card[data-slug="' + s + '"]'); });
      var cheapest = Math.min.apply(null, rows.map(function (r) { return +r.dataset.total; }));
      var fields = [["Estimated total", function (r) { return money(r.dataset.total); }, 1],
        ["Flight (sample)", function (r) { return money(r.dataset.flight); }, 1],
        ["Hotel", function (r) { return money(r.dataset.hotel); }, 1],
        ["Left of budget", function (r) { var l = +r.dataset.left; return l >= 0 ? money(l) : "Over by " + money(-l); }, 1],
        ["Best for", function (r) { return $(".bf", r).textContent; }, 0]];
      var html = "<thead><tr><th scope='col'></th>" + rows.map(function (r) { return "<th scope='col'>" + r.dataset.name + "</th>"; }).join("") + "</tr></thead><tbody>";
      fields.forEach(function (f) {
        html += "<tr><th scope='row'>" + f[0] + "</th>" + rows.map(function (r) {
          var best = f[0] === "Estimated total" && +r.dataset.total === cheapest;
          return "<td class='" + (f[2] ? "mono" : "") + "'>" + f[1](r) + (best ? " (lowest)" : "") + "</td>";
        }).join("") + "</tr>";
      });
      $("#cmp-table").innerHTML = html + "</tbody>";
      if (dlg.showModal) dlg.showModal();
    });
    renderTray();
  }

  /* ---------- Destination: live recalculation, weather, parallax ---------- */
  var det = $("#detail");
  if (det) {
    var f = +det.dataset.flight, h = +det.dataset.hotel, bud = +det.dataset.budget;
    var slider = $("#n");
    function calc() {
      var n = +slider.value, hotel = h * n, total = f + hotel;
      $("#n-out").textContent = n; $("#l-n").textContent = n;
      $("#total").textContent = money(total); $("#l-flight").textContent = money(f); $("#l-hotel").textContent = money(hotel);
      $("#split").style.width = Math.round(f / total * 100) + "%";
      $("#meter").style.width = Math.min(100, Math.round(total / bud * 100)) + "%";
      var v = $("#verdict"), left = bud - total;
      v.className = "verdict " + (left >= 0 ? "ok" : "no");
      v.textContent = left >= 0 ? money(left) + " left of your " + money(bud) + " budget." : "Over your " + money(bud) + " budget by " + money(-left) + ".";
      var u = new URL(location.href); u.searchParams.set("nights", n); history.replaceState(null, "", u);
    }
    slider.addEventListener("input", calc); calc();

    var wx = $("#wx .wx-body"), ctl = new AbortController(), t = setTimeout(function () { ctl.abort(); }, 7000);
    if (window.VH_DEMO) { wx.textContent = "Live weather is part of the full Flask app. This demo shows the trip math only."; ctl.abort(); clearTimeout(t); }
    else fetch("/api/weather/" + det.dataset.slug, { signal: ctl.signal }).then(function (r) { return r.json(); }).then(function (j) {
      clearTimeout(t);
      if (j.error) { wx.textContent = "Live weather isn't available right now. The trip math above still works."; return; }
      wx.innerHTML = "<span class='wx-temp'>" + j.temp + "&deg;F</span><br>" + j.desc +
        "<dl><dt>Feels like</dt><dd>" + j.feels + "&deg;F</dd><dt>Humidity</dt><dd>" + j.humidity + "%</dd><dt>Wind</dt><dd>" + j.wind + " mph</dd></dl>";
    }).catch(function () { wx.textContent = "Live weather isn't available right now. The trip math above still works."; });

    var p = $("#parallax");
    if (p && !reduce) {
      var ticking = false;
      addEventListener("scroll", function () {
        if (ticking) return; ticking = true;
        requestAnimationFrame(function () { p.style.transform = "translate3d(0," + Math.min(scrollY, 800) * 0.25 + "px,0)"; ticking = false; });
      }, { passive: true });
    }
  }
})();
