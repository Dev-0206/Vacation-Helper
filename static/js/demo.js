/* Static demo glue (GitHub Pages). Rebuilds the Flask pages in the browser from window.VH_DATA.
   Used only by tools/build_demo.py output. The real app renders these pages server-side. */
(function () {
  "use strict";
  var D = window.VH_DATA, VIBES = D.vibes, VL = {}; VIBES.forEach(function (v) { VL[v[0]] = v[1]; });
  var qs = new URLSearchParams(location.search), main = document.getElementById("main"), page = document.body.dataset.page;
  function esc(t) { return String(t).replace(/[&<>"]/g, function (c) { return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]; }); }
  function int(v, d, lo, hi) { v = parseInt(v, 10); return isNaN(v) ? d : Math.max(lo, Math.min(hi, v)); }
  var m = function (n) { return "$" + Math.round(n).toLocaleString("en-US"); };
  var trip = {
    origin: (qs.get("origin") || "").replace(/[^a-zA-Z]/g, "").toUpperCase().slice(0, 3),
    budget: int(qs.get("budget"), 1500, 100, 20000), nights: int(qs.get("nights"), 4, 1, 30),
    vibes: qs.getAll("vibe").filter(function (v) { return VL[v]; })
  };
  function tq(extra) {
    var p = new URLSearchParams(); if (trip.origin) p.set("origin", trip.origin);
    p.set("budget", trip.budget); p.set("nights", trip.nights); trip.vibes.forEach(function (v) { p.append("vibe", v); });
    if (extra) Object.keys(extra).forEach(function (k) { p.set(k, extra[k]); });
    return "?" + p.toString();
  }
  function chips(checked, name) {
    return VIBES.map(function (v) { return '<label class="chip"><input type="checkbox" ' + (name ? 'name="vibe" ' : "") + 'value="' + v[0] + '"' + (checked.indexOf(v[0]) > -1 ? " checked" : "") + "><span>" + v[1] + "</span></label>"; }).join("");
  }

  if (page === "home") {
    document.getElementById("origin").value = trip.origin || "SEA";
    document.getElementById("budget").value = trip.budget;
    document.getElementById("budget-r").value = Math.min(trip.budget, 6000);
    document.getElementById("nights").value = trip.nights;
    document.getElementById("vibes").innerHTML = chips(trip.vibes, true);
    var data = D.dest.map(function (d) { return { slug: d.slug, total1: d.flight, hotel: d.hotel, vibes: d.vibes, airport: d.airport }; });
    document.getElementById("dest-data").textContent = JSON.stringify(data);
    document.getElementById("count-lede").textContent = D.dest.length;
  }

  if (page === "results") {
    var items = D.dest.filter(function (d) { return !(trip.origin && d.airport === trip.origin); }).map(function (d) {
      var hotel = d.hotel * trip.nights, total = d.flight + hotel, left = trip.budget - total;
      return Object.assign({}, d, { hotel_total: hotel, total: total, left: left, fits: left >= 0, pct: Math.min(100, Math.round(total / trip.budget * 100)), fpct: Math.round(d.flight / total * 100) });
    });
    var fits = items.filter(function (i) { return i.fits; }).length;
    document.title = "Trips for " + m(trip.budget) + " | Vacation Helper";
    var cards = items.map(function (i) {
      return '<li class="card' + (i.fits ? "" : " over") + '" data-slug="' + i.slug + '" data-name="' + esc(i.name) + '" data-total="' + i.total + '" data-fits="' + (i.fits ? 1 : 0) + '" data-vibes="' + i.vibes.join(",") + '" data-flight="' + i.flight + '" data-hotel="' + i.hotel_total + '" data-left="' + i.left + '">' +
        '<a class="card-link" href="destination.html' + tq({ d: i.slug }) + '" aria-label="' + esc(i.name) + ", estimated " + m(i.total) + ", " + (i.fits ? "fits" : "over") + ' budget">' +
        '<div class="art"><img loading="lazy" src="static/scenes/' + i.slug + '.svg" alt=""><span class="tag ' + (i.fits ? "ok" : "no") + '">' + (i.fits ? "Fits budget" : "Over by " + m(-i.left)) + "</span></div>" +
        '<div class="body"><h2>' + esc(i.name) + ' <span class="code">' + i.airport + '</span></h2><p class="bf">' + esc(i.best_for) + "</p>" +
        '<p class="total">' + m(i.total) + " <span>estimated</span></p>" +
        '<div class="split" role="img" aria-label="Flight ' + m(i.flight) + ", hotel " + m(i.hotel_total) + '"><i style="width:' + i.fpct + '%"></i></div>' +
        '<p class="math">Flight ' + m(i.flight) + " + hotel " + m(i.hotel_total) + "</p>" +
        '<div class="meter" aria-hidden="true"><i style="width:' + i.pct + '%"></i></div>' +
        '<p class="scope">Flight and hotel only. Food, activities, and taxes are not included.</p><p class="left">' + (i.fits ? m(i.left) + " left of budget" : "Over budget by " + m(-i.left)) + "</p></div></a>" +
        '<label class="cmp"><input type="checkbox" class="cmp-box" value="' + i.slug + '"> Compare</label></li>';
    }).join("");
    main.innerHTML = '<section class="wrap"><a class="back" href="index.html' + tq() + '">&larr; Change trip</a>' +
      '<h1 class="display sm"><span id="sum-fit">' + fits + '</span> of <span id="sum-total">' + items.length + "</span> fit " + m(trip.budget) + " for " + trip.nights + " night" + (trip.nights === 1 ? "" : "s") + "</h1>" +
      '<p class="lede">Total = sample flight + hotel &times; ' + trip.nights + ". Taxes, food, and transport are not included.</p>" +
      '<div class="toolbar" id="toolbar"><div class="chips" role="group" aria-label="Filter by vibe">' + chips(trip.vibes) + '</div><div class="tools">' +
      '<label class="sel">Sort <select id="sort"><option value="price">Lowest total</option><option value="left">Most left over</option><option value="name">Name</option></select></label>' +
      '<label class="switch"><input type="checkbox" id="over" checked><span>Show over budget</span></label></div></div>' +
      '<p class="empty" id="empty" hidden>Nothing matches those filters. Clear a vibe or show over-budget trips.</p><ol class="grid" id="grid">' + cards + "</ol></section>" +
      '<div class="tray" id="tray" hidden><span id="tray-n"></span><button class="btn primary" id="tray-go" type="button">Compare</button><button class="btn" id="tray-clear" type="button">Clear</button></div>' +
      '<dialog id="cmp-dialog" aria-labelledby="cmp-h"><form method="dialog"><button class="x" aria-label="Close">&times;</button></form><h2 id="cmp-h">Side by side</h2><div class="tbl-wrap"><table id="cmp-table"></table></div></dialog>';
  }

  if (page === "dest") {
    var d = D.dest.filter(function (x) { return x.slug === qs.get("d"); })[0] || D.dest[0];
    var total = d.flight + d.hotel * trip.nights;
    document.title = d.name + " | Vacation Helper";
    main.innerHTML = '<section class="scene-hero"><img src="static/scenes/' + d.slug + '.svg" alt="" class="parallax" id="parallax"><div class="wrap">' +
      '<a class="back light" href="results.html' + tq() + '">&larr; Back to results</a><p class="eyebrow light">' + d.airport + " &middot; " + esc(d.best_for) + "</p>" +
      '<h1 class="display xl">' + esc(d.name) + '</h1><p class="lede light">' + esc(d.notes) + ".</p></div></section>" +
      '<section class="wrap detail" id="detail" data-flight="' + d.flight + '" data-hotel="' + d.hotel + '" data-budget="' + trip.budget + '" data-slug="' + d.slug + '">' +
      '<div class="panel calc"><h2>Your trip cost</h2><label for="n">Nights: <output id="n-out">' + trip.nights + '</output></label>' +
      '<input class="range" id="n" type="range" min="1" max="30" value="' + trip.nights + '"><p class="big" id="total">' + m(total) + "</p>" +
      '<div class="split lg" role="img" aria-label="Flight versus hotel share"><i id="split" style="width:' + Math.round(d.flight / total * 100) + '%"></i></div>' +
      '<ul class="lines"><li><span>Sample flight</span><b id="l-flight">' + m(d.flight) + '</b></li><li><span>Hotel, <span id="l-n">' + trip.nights + "</span> &times; " + m(d.hotel) + '</span><b id="l-hotel">' + m(d.hotel * trip.nights) + "</b></li></ul>" +
      '<div class="meter" aria-hidden="true"><i id="meter" style="width:' + Math.min(100, Math.round(total / trip.budget * 100)) + '%"></i></div><p id="verdict" class="verdict"></p>' +
      '<h3 class="sub">Where your budget goes</h3><div class="stack" role="img" aria-label="Budget split between flight, hotel, and money left"><i class="s-f" id="s-f"></i><i class="s-h" id="s-h"></i><i class="s-l" id="s-l"></i></div>' +
      '<ul class="legend"><li><i class="s-f"></i>Flight <b id="lg-f"></b></li><li><i class="s-h"></i>Hotel <b id="lg-h"></b></li><li><i class="s-l"></i><span id="lg-lt">Left</span> <b id="lg-l"></b></li></ul>' +
      '<p class="scope">This covers a flight and hotel only. Food, activities, and taxes are not included.</p>' +
      '<p class="fine">Estimates from a sample list. Check real prices before booking.</p></div>' +
      '<div class="panel wx" id="wx" aria-live="polite"><h2>Right now in ' + esc(d.name) + '</h2><p class="wx-body"></p></div>' +
      '<div class="panel book"><h2>Check real prices</h2><p>These numbers are estimates. Google shows current prices for your dates.</p><div class="btn-row"><a class="btn" target="_blank" rel="noopener" href="https://www.google.com/travel/flights?q=' + encodeURIComponent(trip.origin ? "Flights from " + trip.origin + " to " + d.airport : "Flights to " + d.airport) + '">Flights to ' + d.airport + ' &#8599;</a><a class="btn" target="_blank" rel="noopener" href="https://www.google.com/travel/hotels/' + encodeURIComponent(d.name) + '">Hotels in ' + esc(d.name) + ' &#8599;</a></div></div>' +
      '<div class="panel why"><h2>Why it fits</h2><div class="chips static">' + d.vibes.map(function (v) { return '<span class="chip on"><span>' + VL[v] + "</span></span>"; }).join("") + "</div><p>" + esc(d.notes) + ".</p></div></section>";
  }
})();
