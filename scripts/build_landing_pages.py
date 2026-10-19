#!/usr/bin/env python3
"""Build the service landing pages (/car-rental-pune/, /fleet/, ...).

Each page is written to <slug>/index.html using the shared header, footer and
sitewide TaxiService JSON-LD taken from contact.html, so the landing pages
stay identical in chrome to the rest of the site. Edit the PAGES content below
and re-run:

    python3 scripts/build_landing_pages.py
    python3 scripts/update-sitemap.py
"""
import html
import json
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parent.parent
SITE = 'https://bastetravels.com'
PHONE = '+917507958364'
PHONE_TXT = '+91 75079 58364'
BIZ = f'{SITE}/#business'


def wa(text):
    from urllib.parse import quote
    return f'https://wa.me/917507958364?text={quote(text)}'


# ─── Shared fragments ───────────────────────────────────────────────

def stats(items):
    cells = ''.join(f'<div class="rh-stat"><span class="val">{v}</span><span class="lbl">{l}</span></div>' for v, l in items)
    return f'<div class="route-hero-stats">{cells}</div>'


def hero(badge, h1, sub, stat_items, cta_text, wa_text, form_html):
    return f'''<section class="route-hero"><div class="container"><div class="route-hero-grid">
  <div>
    <div class="hero-badge">{badge}</div>
    <h1>{h1}</h1>
    <p class="sub">{sub}</p>
    {stats(stat_items)}
    <div class="hero-cta">
      <a href="tel:{PHONE}" class="btn btn-primary btn-lg">📞 Call {PHONE_TXT}</a>
      <a href="{wa(wa_text)}" target="_blank" rel="noopener" class="btn btn-green btn-lg">💬 {cta_text}</a>
    </div>
  </div>
{form_html}
</div></div></section>'''


def quick_form(title, note, types, frm, to, fare_label=None, fare=None):
    opts = ''.join(f'<option>{t}</option>' for t in types)
    fare_box = (f'<div class="fare-box"><span class="lbl">{fare_label}</span><span class="val">{fare}</span></div>'
                if fare else '<p class="qb-note">We reply on WhatsApp with the car, driver details and full fare.</p>')
    return f'''  <div class="quick-book">
    <div class="quick-book-head"><h2>{title}</h2><p>{note}</p></div>
    <form id="quickBookForm">
      <div class="qb-field"><label for="qb-type">Trip type</label><select id="qb-type" required>{opts}</select></div>
      <div class="qb-field-row">
        <div class="qb-field"><label for="qb-from">From</label><input type="text" id="qb-from" value="{frm}" required></div>
        <div class="qb-field"><label for="qb-to">To</label><input type="text" id="qb-to" value="{to}" placeholder="Drop location" required></div>
      </div>
      <div class="qb-field-row">
        <div class="qb-field"><label for="qb-date">Date</label><input type="date" id="qb-date" required></div>
        <div class="qb-field"><label for="qb-phone">Phone</label><input type="tel" id="qb-phone" placeholder="10-digit mobile" autocomplete="tel" required></div>
      </div>
      <div class="qb-field"><label for="qb-name">Name</label><input type="text" id="qb-name" placeholder="Your name" autocomplete="name" required></div>
      <button type="submit" class="btn btn-primary qb-submit">💬 Get quote on WhatsApp</button>
      {fare_box}
    </form>
  </div>'''


def wa_form(form_name, title, note, fields, button):
    """fields: list of (id, label, type/options, placeholder, required, half)"""
    rows, half = [], []

    def field(fid, label, kind, ph, req):
        r = ' required' if req else ''
        if isinstance(kind, list):
            opts = ''.join(f'<option>{o}</option>' for o in kind)
            ctl = f'<select id="{fid}" data-wa-label="{label}"{r}>{opts}</select>'
        elif kind == 'textarea':
            ctl = f'<textarea id="{fid}" data-wa-label="{label}" rows="3" placeholder="{ph}"{r}></textarea>'
        else:
            ctl = f'<input type="{kind}" id="{fid}" data-wa-label="{label}" placeholder="{ph}"{r}>'
        return f'<div class="qb-field"><label for="{fid}">{label}</label>{ctl}</div>'

    for fid, label, kind, ph, req, is_half in fields:
        if is_half:
            half.append(field(fid, label, kind, ph, req))
            if len(half) == 2:
                rows.append(f'<div class="qb-field-row">{"".join(half)}</div>')
                half = []
        else:
            rows.append(field(fid, label, kind, ph, req))
    if half:
        rows.append(''.join(half))
    return f'''  <div class="quick-book">
    <div class="quick-book-head"><h2>{title}</h2><p>{note}</p></div>
    <form data-wa-form="{form_name}">
      {"".join(rows)}
      <button type="submit" class="btn btn-green qb-submit">💬 {button}</button>
      <p class="qb-note">Opens WhatsApp with your details filled in. Prefer email? Write to <a href="mailto:info@bastetravels.com">info@bastetravels.com</a></p>
    </form>
  </div>'''


def section(tag, h2, body, alt=False, intro=''):
    cls = ' class="alt"' if alt else ''
    intro_html = f'<p>{intro}</p>' if intro else ''
    return f'''<section{cls}><div class="container">
  <div class="section-head"><div class="section-tag">{tag}</div><h2>{h2}</h2>{intro_html}</div>
  {body}
</div></section>'''


def features(items):
    colors = ['background:var(--primary-soft);color:var(--primary)', 'background:var(--green-soft);color:var(--green)',
              'background:var(--orange-soft);color:var(--orange)', 'background:#ede9fe;color:#6d28d9',
              'background:#dbeafe;color:#1d4ed8', 'background:#fee2e2;color:#b91c1c',
              'background:#fef3c7;color:#92400e', 'background:#d1fae5;color:#047857']
    cards = ''.join(f'<div class="feature-card"><div class="feature-icon" style="{colors[i % len(colors)]}" aria-hidden="true">{ic}</div><h3>{t}</h3><p>{d}</p></div>'
                    for i, (ic, t, d) in enumerate(items))
    return f'<div class="features-grid">{cards}</div>'


def steps(items):
    return '<div class="steps-grid">' + ''.join(
        f'<div class="step"><div class="step-num">{i}</div><h3>{t}</h3><p>{d}</p></div>' for i, (t, d) in enumerate(items, 1)) + '</div>'


def zones(items):
    return '<div class="coverage-grid">' + ''.join(
        f'<div class="cov-zone"><span class="tag">{tag}</span><h3>{t}</h3><p>{d}</p></div>' for tag, t, d in items) + '</div>'


def table(head, rows, caption):
    th = ''.join(f'<th scope="col">{h}</th>' for h in head)
    tr = ''.join('<tr>' + ''.join(f'<td>{c}</td>' for c in r) + '</tr>' for r in rows)
    return f'<div class="lp-table-wrap"><table class="lp-table"><caption>{caption}</caption><thead><tr>{th}</tr></thead><tbody>{tr}</tbody></table></div>'


def article(inner):
    return f'<section><div class="container"><div class="article">{inner}</div></div></section>'


def faq(items):
    body = ''.join(f'<details class="faq-item"><summary>{q}</summary><p>{a}</p></details>' for q, a in items)
    return section('FAQ', 'Questions people <span class="hl">ask us</span>', f'<div class="faq-list">{body}</div>', alt=True)


def related(links):
    cards = ''.join(f'<a class="lp-related-card" href="{u}"><strong>{t}</strong><span>{d}</span></a>' for u, t, d in links)
    return section('Related services', 'More ways we can <span class="hl">help</span>', f'<div class="lp-related">{cards}</div>')


def cta(h2, p, wa_text):
    return f'''<section class="cta-section"><div class="container"><div class="cta-inner">
  <h2>{h2}</h2>
  <p>{p}</p>
  <div class="cta-btn-row">
    <a href="tel:{PHONE}" class="btn btn-white btn-lg">📞 Call {PHONE_TXT}</a>
    <a href="{wa(wa_text)}" target="_blank" rel="noopener" class="btn btn-green btn-lg">💬 WhatsApp us</a>
  </div>
  <div class="cta-contact"><a href="mailto:bastetravels@gmail.com">✉ bastetravels@gmail.com</a><a href="/pay.html">💳 Pay online</a></div>
</div></div></section>'''


VEHICLE_SVG = {
    'sedan': '<svg viewBox="0 0 120 48" role="img" aria-label="{alt}"><path d="M8 34c0-5 3-8 9-9l14-2 14-10c3-2 6-3 10-3h20c5 0 8 1 12 4l11 9 10 2c6 1 8 4 8 9v4H8z" fill="currentColor" opacity=".9"/><path d="M48 16h16v9H38zM68 16h12l10 9H68z" fill="#fff" opacity=".85"/><circle cx="30" cy="38" r="7" fill="#0c1a2b"/><circle cx="92" cy="38" r="7" fill="#0c1a2b"/><circle cx="30" cy="38" r="3" fill="#cbd5e1"/><circle cx="92" cy="38" r="3" fill="#cbd5e1"/></svg>',
    'suv': '<svg viewBox="0 0 120 48" role="img" aria-label="{alt}"><path d="M8 36V24c0-4 2-6 6-7l16-3 10-8h50c4 0 7 2 9 5l9 12c3 1 4 3 4 6v7z" fill="currentColor" opacity=".9"/><path d="M42 10h20v11H32zM66 10h20l7 11H66z" fill="#fff" opacity=".85"/><circle cx="30" cy="38" r="8" fill="#0c1a2b"/><circle cx="92" cy="38" r="8" fill="#0c1a2b"/><circle cx="30" cy="38" r="3.5" fill="#cbd5e1"/><circle cx="92" cy="38" r="3.5" fill="#cbd5e1"/></svg>',
    'van': '<svg viewBox="0 0 120 48" role="img" aria-label="{alt}"><path d="M6 36V12c0-4 2-6 6-6h78c5 0 8 2 11 6l9 12c3 2 4 4 4 7v5z" fill="currentColor" opacity=".9"/><path d="M14 12h16v10H14zM34 12h16v10H34zM54 12h16v10H54zM74 12h16v10H74zM94 12l8 10h-8z" fill="#fff" opacity=".85"/><circle cx="28" cy="38" r="7" fill="#0c1a2b"/><circle cx="94" cy="38" r="7" fill="#0c1a2b"/><circle cx="28" cy="38" r="3" fill="#cbd5e1"/><circle cx="94" cy="38" r="3" fill="#cbd5e1"/></svg>',
}

# ─── Page content ───────────────────────────────────────────────────

AREAS_EAST = [
    ('HQ', 'Hadapsar', 'Our base. Fastest pickups for Hadapsar, Amanora, SP Infocity and Phursungi. Pune Airport is about 13 km away.'),
    ('IT hub', 'Magarpatta City', 'Regular pickups from Magarpatta City and Cybercity offices and residences, minutes from our Hadapsar base.'),
    ('IT hub', 'Kharadi', 'EON IT Park, World Trade Center Pune and Kharadi residential towers. About 8 km from Pune Airport.'),
    ('Airport belt', 'Viman Nagar &amp; Kalyani Nagar', 'Hotels and homes closest to Pune Airport, plus Koregaon Park and Yerawada.'),
    ('West Pune', 'Hinjewadi, Wakad &amp; Baner', 'Rajiv Gandhi Infotech Park and the western suburbs. Plan extra time for Hinjewadi traffic at shift change.'),
    ('City', 'Camp, Shivajinagar &amp; Pune Station', 'Railway station and bus stand pickups, and central Pune hotels.'),
]

PAGES = [
# 1 ─────────────────────────────────────────────────────────────────
dict(
    slug='car-rental-pune',
    crumb='Car Rental in Pune',
    title='Car Rental in Pune with Driver | Baste Travels',
    desc='Car rental in Pune with a verified driver: 8 hr / 12 hr local hire, airport transfers, outstation at ₹12/km and monthly rental. WhatsApp +91 75079 58364.',
    keyword='car rental in Pune',
    service=dict(name='Car Rental in Pune with Driver', type='Car rental with driver'),
    body=lambda: hero(
        '🚗 Chauffeur-driven · Hadapsar, Pune',
        'Car Rental in Pune <span class="hl">with a Verified Driver</span>',
        'Hire a clean, AC car with a police-verified driver for a few hours, a full day, an airport run, an outstation trip or a whole month. One call or WhatsApp and we confirm the car, driver and fare.',
        [('8 / 12 hr', 'Local packages'), ('₹12/km', 'Outstation'), ('24×7', 'Bookings'), ('4–17', 'Seats')],
        'WhatsApp for car rental', 'Hi Baste Travels, I want to rent a car with driver in Pune',
        quick_form('Rent a car in Pune', 'Tell us the trip, we send the fare', ['Local 8 hr rental', 'Local 12 hr rental', 'Airport transfer', 'Outstation trip', 'Monthly rental'], 'Pune', '')
    ) + article('''
<h2>Car hire in Pune, the way you need it</h2>
<p>Baste Travels is a Pune car rental service based in <strong>Hadapsar</strong>. Every rental comes with a verified driver, so you do not have to deal with Pune traffic, parking or highway navigation. You choose the car and the time; we handle the rest.</p>
<h3>Local rental: 8 hours or 12 hours</h3>
<p>Book a car and driver for a block of time inside Pune and PCMC: office visits across Kharadi and Hinjewadi, hospital appointments, shopping, family functions or a sightseeing day. The car stays with you and waits between stops. We quote the package up front on WhatsApp, including the kilometres covered and the rate for extra hours or kilometres.</p>
<h3>Airport transfers</h3>
<p>Pickups and drops at <a href="/pune-airport-taxi/">Pune Airport (Lohegaon)</a> and long-distance transfers to <a href="/pune-to-mumbai-airport/">Mumbai Airport T1 and T2</a>. We track your flight, so a late landing does not cost you extra.</p>
<h3>Outstation trips</h3>
<p>One-way and round trips from Pune to anywhere in Maharashtra at a flat <strong>₹12/km</strong> with a 300 km minimum billing, tolls extra. See <a href="/outstation-cab-service-pune/">outstation cab service</a> for fares on popular routes.</p>
<h3>Monthly rental</h3>
<p>A dedicated car and driver for a month or longer for executives, families and businesses. Details on the <a href="/monthly-car-rental-pune/">monthly car rental</a> page.</p>
<div class="highlight-box"><p><strong>Which car?</strong> Sedans seat 4, SUVs 6–7 and Tempo Travellers 12–17. Compare them on our <a href="/fleet/">fleet page</a>.</p></div>
''') + section('Pickup areas', 'Where we pick up <span class="hl">most often</span>', zones(AREAS_EAST), alt=True,
              intro='We serve all of Pune and Pimpri-Chinchwad. These are the areas closest to our Hadapsar base or where we run regular trips.')
    + section('Why Baste Travels', 'What every rental <span class="hl">includes</span>', features([
        ('👮', 'Verified driver', 'Police-verified drivers with a commercial licence and medical fitness certificate.'),
        ('📄', 'Legal paperwork', 'Commercial permit, insurance and the other documents a commercial cab must carry, in the car.'),
        ('❄️', 'Clean AC car', 'Cars are cleaned before each trip. AC is included in the fare.'),
        ('🚫', 'No alcohol, no smoking', 'Strict code for every driver, on every trip.'),
        ('📍', 'Live location', 'Share the trip with family on request.'),
        ('🧾', 'Clear quote', 'Fare, inclusions and extra-hour or extra-km rates are confirmed before you travel.'),
        ('🕐', '24×7 bookings', 'Early-morning flights and late-night returns are routine for us.'),
        ('💳', 'Easy payment', 'UPI, cash, or pay online. GST invoices for companies.'),
    ]))
    + section('How to book', 'Book in <span class="hl">three steps</span>', steps([
        ('Send your trip', f'Call or WhatsApp {PHONE_TXT} with pickup, time, and where you need to go.'),
        ('Get the fare', 'We confirm the car, the package, and what is included. No surprises later.'),
        ('Travel', 'Your driver arrives on time with the car. You receive the driver details in advance.'),
    ]), alt=True),
    faqs=[
        ('Do you rent cars without a driver (self-drive)?', 'Every Baste Travels rental is chauffeur-driven. A verified driver comes with each car, which also covers parking, navigation and the commercial permit the car needs.'),
        ('How much does car rental in Pune cost?', 'Outstation trips are ₹12/km with a 300 km minimum billing, tolls extra. Local 8 hr and 12 hr packages and airport transfers are quoted for your exact pickup and timing; WhatsApp us and we reply with the full fare in minutes.'),
        ('Can I book a car for a full day inside Pune?', 'Yes. Choose an 8 hour or 12 hour local package. The car and driver stay with you for multiple stops anywhere in Pune and Pimpri-Chinchwad.'),
        ('Which areas of Pune do you cover?', 'All of Pune and PCMC. We are based in Hadapsar, so Hadapsar, Magarpatta, Kharadi, Viman Nagar and Koregaon Park get the quickest pickups. We also serve Hinjewadi, Wakad, Baner and Aundh daily.'),
        ('Can I get a GST invoice?', 'Yes. Share your company name and GSTIN when you book and we issue a GST invoice.'),
    ],
    related=[('/pune-airport-taxi/', 'Pune Airport Taxi', 'Pickups and drops at Lohegaon'), ('/monthly-car-rental-pune/', 'Monthly Car Rental', 'Dedicated car and driver'),
             ('/outstation-cab-service-pune/', 'Outstation Cabs', '₹12/km across Maharashtra'), ('/fleet/', 'Our Fleet', 'Sedan, SUV, Tempo Traveller')],
    cta=('Need a car in Pune today?', 'Call or WhatsApp now. We confirm the car, driver and fare in minutes.', 'Hi Baste Travels, I need a car with driver in Pune'),
),
# 2 ─────────────────────────────────────────────────────────────────
dict(
    slug='pune-airport-taxi',
    crumb='Pune Airport Taxi',
    title='Pune Airport Taxi 24×7 | Pickup &amp; Drop | Baste Travels',
    desc='Pune Airport taxi for pickup and drop at Lohegaon (PNQ). Flight tracking, verified drivers, 24×7 from Hadapsar, Kharadi, Magarpatta and all of Pune.',
    keyword='Pune airport taxi',
    service=dict(name='Pune Airport Taxi', type='Airport transfer'),
    body=lambda: hero(
        '✈️ Pune International Airport · PNQ',
        'Pune Airport Taxi <span class="hl">Pickup &amp; Drop, 24×7</span>',
        'Reliable cabs to and from Pune Airport at Lohegaon for early flights, late arrivals and everything in between. We track your flight and your driver is there when you land.',
        [('24×7', 'Every flight'), ('Tracked', 'Flight status'), ('~13 km', 'From Hadapsar'), ('4–17', 'Seats')],
        'WhatsApp for airport taxi', 'Hi Baste Travels, I need a Pune Airport taxi',
        quick_form('Book an airport transfer', 'Pickup or drop at Pune Airport', ['Drop to Pune Airport', 'Pickup from Pune Airport'], '', 'Pune Airport (PNQ)')
    ) + article('''
<h2>Airport transfers to and from Lohegaon</h2>
<p>Pune International Airport (PNQ) is in <strong>Lohegaon</strong>, north-east of the city. Baste Travels runs airport pickups and drops around the clock from our base in Hadapsar, with most trips starting in east Pune: Hadapsar, Magarpatta, Kharadi, Viman Nagar and Koregaon Park.</p>
<h3>Arriving in Pune</h3>
<p>Send us your flight number when you book. We track the flight, so if it lands late your driver adjusts and you are not charged for the delay. Your driver's name and number reach you on WhatsApp before you land, and the driver meets you outside arrivals.</p>
<h3>Flying out of Pune</h3>
<p>For domestic flights, airlines generally ask you to be at the terminal two hours before departure; for international flights, three hours. We plan the pickup time with you based on your area and the time of day, with a buffer for traffic on Nagar Road and the airport approach.</p>
<h2>Typical distances to Pune Airport</h2>
''' + table(['Pickup area', 'Approx. distance', 'Notes'], [
        ['Viman Nagar', '4 km', 'Closest residential area to the terminal'],
        ['Kharadi (EON IT Park, WTC)', '8 km', 'Via Nagar Road'],
        ['Koregaon Park / Kalyani Nagar', '9 km', 'Popular hotel area'],
        ['Magarpatta City', '11 km', 'Via Mundhwa'],
        ['Hadapsar', '13 km', 'Our base'],
        ['Pune Station / Camp', '10 km', ''],
        ['Baner / Aundh', '20 km', 'Allow extra time at peak hours'],
        ['Hinjewadi', '30 km', 'Allow extra time at peak hours'],
    ], 'Road distances are approximate and vary with the exact address and route.') + '''
<div class="highlight-box"><p><strong>Fares:</strong> airport transfers are quoted for your pickup address, time and car type. WhatsApp your details and we reply with the full fare. Waiting after landing follows our <a href="/terms-and-conditions.html">terms</a>: the first 10 minutes are free.</p></div>
<h2>Connecting onward from Pune Airport</h2>
<p>Landing in Pune and travelling on? We drive you straight from the terminal to <a href="/pune-to-mumbai-cab.html">Mumbai</a>, <a href="/pune-to-lonavala-cab.html">Lonavala</a>, <a href="/pune-to-mahabaleshwar-cab.html">Mahabaleshwar</a> or <a href="/pune-to-shirdi-cab.html">Shirdi</a> at our standard outstation rate of ₹12/km.</p>
''') + section('Why book with us', 'Airport runs <span class="hl">done right</span>', features([
        ('✈️', 'Flight tracking', 'A delayed landing does not cost you extra waiting.'),
        ('📲', 'Driver details in advance', 'Name, phone and car number on WhatsApp before pickup.'),
        ('🌙', 'Night and early flights', '2 AM arrivals and 4 AM departures are routine for us.'),
        ('🧳', 'Room for luggage', 'Choose an SUV or Tempo Traveller for families and groups.'),
    ]), alt=True)
    + section('Pickup areas', 'Airport pickups <span class="hl">across Pune</span>', zones(AREAS_EAST)),
    faqs=[
        ('How early should I leave for Pune Airport?', 'Airlines generally ask you to reach the terminal two hours before a domestic flight and three hours before an international one. From Hadapsar or Magarpatta, plan 30 to 45 minutes of driving; from Hinjewadi or Baner, plan more at peak hours. We suggest the pickup time when you book.'),
        ('What if my flight is delayed?', 'We track your flight number, so your driver arrives for the actual landing time. You are not charged for a delay in the flight.'),
        ('Where does the driver meet me?', 'Outside the arrivals exit. Your driver calls you once you are through baggage claim.'),
        ('How much is a taxi from Hadapsar to Pune Airport?', 'Airport fares depend on the exact pickup address, time and car. WhatsApp us your address and flight time and we send the full fare in minutes.'),
        ('Do you have bigger cars for families?', 'Yes. Ertiga or Innova Crysta for 6 to 7 people and a Tempo Traveller for 12 to 17. See our fleet page.'),
    ],
    related=[('/pune-to-mumbai-airport/', 'Pune to Mumbai Airport', 'T1 and T2 transfers'), ('/car-rental-pune/', 'Car Rental in Pune', 'Local 8 hr / 12 hr hire'),
             ('/corporate-employee-transport/', 'Corporate Transport', 'Employee and guest transfers'), ('/fleet/', 'Our Fleet', 'Choose the right car')],
    cta=('Flying in or out of Pune?', 'Book your airport taxi now. Driver details arrive on WhatsApp before pickup.', 'Hi Baste Travels, I need a Pune Airport taxi'),
),
# 3 ─────────────────────────────────────────────────────────────────
dict(
    slug='pune-to-mumbai-airport',
    crumb='Pune to Mumbai Airport Taxi',
    title='Pune to Mumbai Airport Taxi T1 &amp; T2 | ₹3,600 | Baste Travels',
    desc='Pune to Mumbai Airport taxi to T1 and T2 at ₹12/km, ₹3,600 minimum fare, tolls extra. Verified drivers, 24×7 departures planned around your flight.',
    keyword='Pune to Mumbai airport taxi',
    service=dict(name='Pune to Mumbai Airport Taxi', type='Airport transfer', price='3600'),
    body=lambda: hero(
        '✈️ Pune → Mumbai Airport (BOM)',
        'Pune to Mumbai Airport Taxi <span class="hl">T1 &amp; T2</span>',
        'Door-to-terminal cabs from anywhere in Pune to Mumbai Airport, day or night. Flat ₹12/km with a verified driver, planned around your flight time.',
        [('~160 km', 'Distance'), ('3–4 hr', 'Typical drive'), ('₹12', 'Per km'), ('₹3,600', 'Min fare')],
        'WhatsApp for Mumbai Airport cab', 'Hi Baste Travels, I need a Pune to Mumbai Airport taxi',
        quick_form('Book Pune → Mumbai Airport', 'Tell us your flight time', ['One-way to Mumbai Airport', 'Pickup from Mumbai Airport to Pune'], 'Pune', 'Mumbai Airport T2', 'Minimum fare (tolls extra)', '₹3,600')
    ) + article('''
<h2>Pune to Mumbai Airport, without the stress</h2>
<p>Mumbai's Chhatrapati Shivaji Maharaj International Airport (BOM) is roughly <strong>150–170 km</strong> from Pune depending on where you start, almost all of it on the Mumbai–Pune Expressway. International flights use Terminal 2 (T2); domestic flights use T1 or T2 depending on the airline. Tell us your airline and flight number and we drop you at the right terminal.</p>
<div class="highlight-box"><p><strong>Fare:</strong> ₹12/km with a 300 km minimum billing, so a one-way Pune to Mumbai Airport trip is <strong>₹3,600</strong>. Expressway and city tolls are paid separately at the booth. AC, driver and fuel are included.</p></div>
<h2>When to leave Pune</h2>
<p>The drive usually takes 3 to 4 hours, longer at Mumbai peak hours or in heavy monsoon rain. Add the airline's reporting time on top: about two hours for domestic and three hours for international flights. As a rule of thumb, leave Pune <strong>6 to 7 hours before an international departure</strong> and 5 to 6 hours before a domestic one. We confirm a pickup time with you when you book.</p>
''' + table(['Flight departs (BOM)', 'Domestic: leave Pune by', 'International: leave Pune by'], [
        ['6:00 AM', '12:30 AM', '11:30 PM (previous night)'],
        ['10:00 AM', '4:30 AM', '3:30 AM'],
        ['2:00 PM', '8:30 AM', '7:30 AM'],
        ['9:00 PM', '3:30 PM', '2:30 PM'],
    ], 'Suggested departure times from central or east Pune, including traffic buffer. We adjust for your exact pickup area.') + '''
<h2>Mumbai Airport to Pune</h2>
<p>Landing in Mumbai? We pick you up at T1 or T2 and drive you to any address in Pune. Share your flight number so we can track the arrival.</p>
<h2>Good to know</h2>
<ul>
<li>Pickup from any Pune area, including Hadapsar, Magarpatta, Kharadi, Hinjewadi and PCMC.</li>
<li>Sedan for up to 4 travellers with luggage; SUV or Tempo Traveller for families and groups.</li>
<li>Comfort stop at a Food Mall on the expressway on request.</li>
<li>Also going to Mumbai city? See our <a href="/pune-to-mumbai-cab.html">Pune to Mumbai cab</a> page.</li>
</ul>
''') + section('Why travellers choose us', 'Built for <span class="hl">flight days</span>', features([
        ('🕐', 'Planned pickup time', 'We work back from your flight and terminal so you are not rushing.'),
        ('🌙', 'Overnight departures', 'Midnight and 3 AM pickups for early international flights are routine.'),
        ('👮', 'Verified driver', 'Police-verified, experienced on the expressway.'),
        ('💰', 'Flat fare', '₹3,600 minimum fare, no surge at night or on holidays.'),
    ]), alt=True),
    faqs=[
        ('What is the taxi fare from Pune to Mumbai Airport?', 'We charge ₹12/km with a 300 km minimum billing, so the one-way fare is ₹3,600. Tolls are extra and paid at the booth.'),
        ('How long does Pune to Mumbai Airport take?', 'Usually 3 to 4 hours on the Mumbai–Pune Expressway. Allow more time at Mumbai peak hours and in heavy rain.'),
        ('Which terminal will you drop me at?', 'International flights use Terminal 2. Most domestic flights also use T2, but some airlines operate from T1. Share your airline and flight number and we drop you at the correct terminal.'),
        ('Do you do Mumbai Airport to Pune pickups?', 'Yes. We track your flight and pick you up at T1 or T2 for a drop anywhere in Pune.'),
        ('Can I book a night pickup for an early flight?', 'Yes, we operate 24×7. Many of our Mumbai Airport trips leave Pune between midnight and 4 AM.'),
    ],
    related=[('/pune-airport-taxi/', 'Pune Airport Taxi', 'Lohegaon pickups and drops'), ('/pune-to-mumbai-cab.html', 'Pune to Mumbai Cab', 'City drops across Mumbai'),
             ('/outstation-cab-service-pune/', 'Outstation Cabs', 'All routes from Pune'), ('/fleet/', 'Our Fleet', 'Sedan, SUV, Tempo Traveller')],
    cta=('Catching a flight from Mumbai?', 'Send your flight time and pickup area. We reply with a pickup plan and the fare.', 'Hi Baste Travels, I need a Pune to Mumbai Airport taxi'),
),
# 4 ─────────────────────────────────────────────────────────────────
dict(
    slug='corporate-employee-transport',
    crumb='Corporate Employee Transport',
    title='Employee Transportation Services in Pune | Baste Travels',
    desc='Employee transport in Pune: shift pickup and drop, night-shift support, monthly GST billing. Kharadi, Magarpatta, Hadapsar, Hinjewadi. Request a quote.',
    keyword='employee transportation services in Pune',
    service=dict(name='Corporate Employee Transportation in Pune', type='Employee transportation'),
    body=lambda: hero(
        '🏢 For HR, admin and facility teams',
        'Employee Transportation <span class="hl">in Pune</span>',
        'Shift-based pickup and drop for your teams, executive and guest transfers, and event transport. Verified drivers, night-shift safety measures and monthly GST billing from a Hadapsar-based operator.',
        [('Monthly', 'Contracts'), ('GST', 'Invoicing'), ('24×7', 'Shift cover'), ('4–17', 'Seats per vehicle')],
        'WhatsApp for corporate quote', 'Hi Baste Travels, I want a quote for employee transportation',
        wa_form('Corporate transport quote', 'Request a corporate quote', 'We reply on WhatsApp with next steps',
                [('ct-company', 'Company', 'text', 'Company name', True, False),
                 ('ct-name', 'Your name', 'text', 'Name', True, True),
                 ('ct-phone', 'Phone', 'tel', '10-digit mobile', True, True),
                 ('ct-office', 'Office location', ['Kharadi', 'Magarpatta / Hadapsar', 'Hinjewadi', 'Viman Nagar / Yerawada', 'Baner / Aundh', 'Other'], '', True, True),
                 ('ct-staff', 'Employees to transport', ['Under 10', '10–25', '25–50', '50–100', '100+'], '', True, True),
                 ('ct-need', 'What you need', 'textarea', 'Shift timings, pickup areas, start date, night shifts...', False, False)],
                'Send quote request')
    ) + article('''
<h2>Transport your teams can rely on</h2>
<p>Baste Travels runs corporate transport from <strong>Hadapsar</strong>, minutes from Magarpatta City and SP Infocity and a short drive from the Kharadi IT corridor. We work with companies that need dependable shift transport without the overhead of managing vehicles and drivers themselves.</p>
<h3>What we provide</h3>
<ul>
<li><strong>Shift pickup and drop:</strong> fixed routes for morning, general and night shifts, with planned pickup points and times.</li>
<li><strong>Executive and guest transfers:</strong> airport pickups, client visits and inter-office trips in sedans or premium sedans.</li>
<li><strong>Outstation and offsites:</strong> SUVs and Tempo Travellers for team outings and offsites across Maharashtra.</li>
<li><strong>Monthly dedicated vehicles:</strong> a car and driver assigned to your office. See <a href="/monthly-car-rental-pune/">monthly car rental</a>.</li>
</ul>
<h3>Night-shift safety</h3>
<p>Tell us your night-shift policy and we run trips to match it, for example routing so a woman employee is not the last drop, sharing live trip tracking with your transport desk, and having the driver wait until each employee is inside. Every driver is police-verified and follows our <a href="/driver-code-of-conduct.html">driver code of conduct</a> and no-alcohol policy.</p>
<h3>Billing and compliance</h3>
<p>One monthly invoice with GST, trip logs on request, and a single point of contact for changes. Vehicles carry their commercial permit, insurance and fitness documents.</p>
''') + section('IT parks', 'Offices we <span class="hl">serve</span>', zones([
        ('Kharadi', 'EON IT Park &amp; World Trade Center', 'Daily pickups across Kharadi, Wagholi and Viman Nagar.'),
        ('Hadapsar', 'Magarpatta City &amp; Cybercity', 'Our home turf. Short dead-mileage means sharper pricing.'),
        ('Hadapsar', 'SP Infocity', 'Phursungi and Hadapsar industrial area.'),
        ('Hinjewadi', 'Rajiv Gandhi Infotech Park', 'Phases 1–3, with routes from Wakad, Baner and Aundh.'),
        ('Yerawada', 'Commerzone &amp; Airport Road', 'Offices between Kalyani Nagar and the airport.'),
        ('Anywhere', 'Other Pune and PCMC offices', 'Tell us your location and shift pattern for a route plan.'),
    ]), alt=True)
    + section('How we start', 'From enquiry to <span class="hl">first shift</span>', steps([
        ('Share requirements', 'Headcount, shifts, office location and where employees live.'),
        ('Route plan and quote', 'We propose vehicles, routes and a monthly price.'),
        ('Trial period', 'Start small if you prefer, and adjust timings with your team.'),
        ('Go live', 'Monthly billing with GST, one contact for changes.'),
    ]))
    + section('Why companies choose us', 'Fewer escalations, <span class="hl">simpler admin</span>', features([
        ('👮', 'Verified drivers', 'Police verification, commercial licence, medical fitness.'),
        ('🌙', 'Night-shift support', 'Routing and drop confirmation built around your safety policy.'),
        ('🧾', 'GST invoicing', 'One monthly invoice with trip details.'),
        ('📞', 'Single contact', 'Direct line to the operator, not a call centre.'),
    ]), alt=True),
    faqs=[
        ('What does employee transportation in Pune cost?', 'It depends on headcount, number of shifts, distances and vehicle type. Send your requirements through the form or WhatsApp and we prepare a monthly quote.'),
        ('Do you provide GST invoices?', 'Yes. We bill monthly with GST and can share trip logs with each invoice.'),
        ('How do you handle night shifts for women employees?', 'We follow your company\'s night-shift policy. Common measures we run are routing so a woman employee is not dropped last, sharing live tracking with your transport desk, and drivers waiting until the employee is safely inside.'),
        ('Can you start with a small team?', 'Yes. We work with teams from a handful of employees to larger shift operations, and can add vehicles as you grow.'),
        ('Which areas do you cover?', 'All of Pune and PCMC, including Kharadi, Magarpatta, Hadapsar, Viman Nagar, Yerawada, Hinjewadi, Baner and Wakad.'),
    ],
    related=[('/monthly-car-rental-pune/', 'Monthly Car Rental', 'Dedicated car and driver'), ('/pune-airport-taxi/', 'Pune Airport Taxi', 'Guest and executive pickups'),
             ('/fleet/', 'Our Fleet', 'Vehicles for every team size'), ('/verified-cab-service-pune.html', 'Verified Cab ₹1/km', 'Safety assurance service')],
    cta=('Planning employee transport?', 'Send your shift details and we will propose routes and a monthly price.', 'Hi Baste Travels, I want a quote for employee transportation'),
),
# 5 ─────────────────────────────────────────────────────────────────
dict(
    slug='monthly-car-rental-pune',
    crumb='Monthly Car Rental in Pune',
    title='Monthly Car Rental in Pune with Driver | Baste Travels',
    desc='Monthly car rental in Pune with a dedicated driver for executives, families and businesses. Sedan, SUV or Tempo Traveller, clear package, GST invoice.',
    keyword='monthly car rental in Pune',
    service=dict(name='Monthly Car Rental in Pune with Driver', type='Monthly car rental with driver'),
    body=lambda: hero(
        '📅 Dedicated car + driver',
        'Monthly Car Rental <span class="hl">in Pune with Driver</span>',
        'A dedicated car and verified driver for a month or longer. For executives, families, visiting NRIs and businesses who want a car on call without buying one.',
        [('1 month+', 'Minimum'), ('Same', 'Driver daily'), ('GST', 'Invoice'), ('4–17', 'Seats')],
        'WhatsApp for monthly rental', 'Hi Baste Travels, I want to enquire about monthly car rental in Pune',
        wa_form('Monthly car rental enquiry', 'Get a monthly quote', 'Tell us how you will use the car',
                [('mr-name', 'Your name', 'text', 'Name', True, True),
                 ('mr-phone', 'Phone', 'tel', '10-digit mobile', True, True),
                 ('mr-car', 'Car type', ['Sedan (4 seats)', 'SUV (6–7 seats)', 'Premium sedan', 'Tempo Traveller (12–17)'], '', True, True),
                 ('mr-start', 'Start date', 'date', '', True, True),
                 ('mr-use', 'Daily usage', 'textarea', 'Days per month, daily hours, usual routes...', False, False)],
                'Send enquiry')
    ) + article('''
<h2>A car on call, every day of the month</h2>
<p>Monthly rental gives you the convenience of your own car and driver without the purchase, insurance, maintenance or driver management. Baste Travels assigns a car and a regular driver for your contract period, based out of our Hadapsar office.</p>
<h3>Who it suits</h3>
<ul>
<li><strong>Executives and expats</strong> on a Pune assignment who need daily office travel and weekend trips.</li>
<li><strong>Families</strong> with elderly parents, school runs or regular hospital visits.</li>
<li><strong>NRIs visiting Pune</strong> for a few weeks or months.</li>
<li><strong>Businesses</strong> that need a dedicated vehicle for a manager, a site or a project. For shift transport see <a href="/corporate-employee-transport/">employee transportation</a>.</li>
</ul>
<h3>How the monthly package works</h3>
<p>We build the package around how you will use the car: the number of days per month, daily duty hours and expected kilometres. The quote states clearly what is included (car, driver, fuel within the package, maintenance) and the rate for extra hours or kilometres, so your monthly bill is predictable. Tolls and parking during your trips are charged as actuals.</p>
<div class="highlight-box"><p><strong>Need it for less than a month?</strong> Use our <a href="/car-rental-pune/">8 hr or 12 hr local rental</a> by the day instead.</p></div>
<h3>Choosing the car</h3>
<p>Most monthly clients choose a sedan such as the Swift Dzire. Families and executives often prefer an SUV (Ertiga or Innova Crysta) or a premium sedan (Honda City or Ciaz). Compare them on the <a href="/fleet/">fleet page</a>.</p>
''') + section('What is included', 'Everything handled <span class="hl">for you</span>', features([
        ('🧑‍✈️', 'Regular driver', 'The same verified driver on most days, with a trained replacement on leave days.'),
        ('🔧', 'Maintenance', 'Servicing and repairs are our job. A replacement car is arranged if needed.'),
        ('📄', 'Commercial papers', 'Permit, insurance and fitness documents kept current.'),
        ('🧾', 'One monthly bill', 'GST invoice with a log of extra hours or kilometres.'),
    ]), alt=True)
    + section('How to start', 'Three steps to <span class="hl">your monthly car</span>', steps([
        ('Tell us your usage', 'Days, hours, typical routes and preferred car.'),
        ('Get the package', 'We send a monthly quote with inclusions and extra rates.'),
        ('Start driving', 'Your car and driver report on the start date.'),
    ])),
    faqs=[
        ('What is the minimum period for monthly rental?', 'One month. Shorter needs are better served by our daily 8 hr or 12 hr local packages.'),
        ('Is the driver the same every day?', 'We assign a regular driver for your contract. On the driver\'s weekly off or leave we send a trained, verified replacement.'),
        ('Is fuel included?', 'The monthly package is quoted with fuel for the agreed kilometres. Kilometres beyond the package are billed at the rate stated in your quote.'),
        ('Can a company take a monthly car?', 'Yes. We issue a monthly GST invoice in the company name.'),
        ('Can I use the car outside Pune?', 'Yes, with notice. Outstation days are billed as agreed in your package, plus tolls.'),
    ],
    related=[('/car-rental-pune/', 'Car Rental in Pune', 'Daily 8 hr / 12 hr hire'), ('/corporate-employee-transport/', 'Corporate Transport', 'Shift pickup and drop'),
             ('/fleet/', 'Our Fleet', 'Pick the right car'), ('/pune-airport-taxi/', 'Pune Airport Taxi', 'Airport pickups and drops')],
    cta=('Want a car and driver for the month?', 'Share your usage and we will send a clear monthly package.', 'Hi Baste Travels, I want to enquire about monthly car rental in Pune'),
),
# 6 ─────────────────────────────────────────────────────────────────
dict(
    slug='outstation-cab-service-pune',
    crumb='Outstation Cab Service',
    title='Outstation Cab from Pune at ₹12/km | One Way &amp; Round Trip',
    desc='Outstation cab from Pune at a flat ₹12/km: one-way and round trips to Mumbai, Shirdi, Nashik, Goa and all of Maharashtra. 300 km minimum, tolls extra.',
    keyword='outstation cab from Pune',
    service=dict(name='Outstation Cab Service from Pune', type='Outstation taxi', unit_price='12'),
    body=lambda: hero(
        '🛣️ One way · Round trip · Multi-day',
        'Outstation Cab <span class="hl">from Pune at ₹12/km</span>',
        'One flat rate for every route: ₹12 per kilometre with a verified driver and AC car. One-way drops, round trips and multi-day tours across Maharashtra and to neighbouring states.',
        [('₹12', 'Per km'), ('300 km', 'Min billing'), ('₹3,600', 'Min fare'), ('24×7', 'Departures')],
        'WhatsApp for outstation cab', 'Hi Baste Travels, I want to book an outstation cab from Pune',
        quick_form('Book an outstation cab', 'One-way or round trip', ['One-Way Outstation', 'Round Trip', 'Multi-day tour'], 'Pune', '', 'Minimum fare (tolls extra)', '₹3,600')
    ) + article('''
<h2>How outstation pricing works</h2>
<p>Baste Travels charges a flat <strong>₹12 per km</strong> for outstation trips, with a minimum billing of <strong>300 km</strong>. Shorter trips are billed as 300 km (₹3,600); longer trips are billed on actual distance. Tolls are paid separately at the booth. There is no surge at night, on weekends or during festivals.</p>
''' + table(['Route', 'Distance', 'Typical drive', 'One-way fare'], [
        ['<a href="/pune-to-mumbai-cab.html">Pune → Mumbai</a>', '150 km', '2.5–3 hr', '₹3,600'],
        ['<a href="/pune-to-lonavala-cab.html">Pune → Lonavala</a>', '65 km', '1.5 hr', '₹3,600'],
        ['<a href="/pune-to-mahabaleshwar-cab.html">Pune → Mahabaleshwar</a>', '120 km', '3 hr', '₹3,600'],
        ['<a href="/pune-to-shirdi-cab.html">Pune → Shirdi</a>', '185 km', '4–4.5 hr', '₹3,600'],
        ['<a href="/pune-to-nashik-cab.html">Pune → Nashik</a>', '210 km', '4 hr', '₹3,600'],
        ['<a href="/pune-to-kolhapur-cab.html">Pune → Kolhapur</a>', '230 km', '4.5 hr', '₹3,600'],
        ['<a href="/pune-to-aurangabad-cab.html">Pune → Aurangabad</a>', '240 km', '5 hr', '₹3,600'],
        ['<a href="/pune-to-solapur-cab.html">Pune → Solapur</a>', '250 km', '5 hr', '₹3,600'],
        ['<a href="/pune-to-goa-cab.html">Pune → Goa</a>', '440 km', '8 hr', '₹5,280'],
        ['<a href="/pune-to-nagpur-cab.html">Pune → Nagpur</a>', '700 km', '12 hr', '₹8,400'],
    ], 'One-way fares at ₹12/km with 300 km minimum billing. Tolls extra. Distances are approximate.') + '''
<p>See all <a href="/routes.html">18 routes</a>, including Mumbai and Nashik departures.</p>
<h2>One-way, round trip or multi-day</h2>
<h3>One-way drop</h3>
<p>Pay for the trip you take. Ideal for airport connections, relocations and single-direction business travel.</p>
<h3>Round trip</h3>
<p>The same car and driver take you there and back, waiting while you work, attend a wedding or visit a temple. Billed on total kilometres at ₹12/km.</p>
<h3>Multi-day tours</h3>
<p>Ashtavinayak, Konkan coast, hill stations or a business circuit across several cities. The driver stays with you; food and stay for the driver on overnight trips are agreed at booking.</p>
<div class="highlight-box"><p><strong>Need a bigger car?</strong> The ₹12/km rate is for our standard sedan. SUVs and Tempo Travellers are quoted on request; see the <a href="/fleet/">fleet</a>.</p></div>
''') + section('Included in the fare', 'What ₹12/km <span class="hl">covers</span>', features([
        ('🧑‍✈️', 'Driver', 'Verified, highway-experienced driver.'),
        ('⛽', 'Fuel', 'Fuel for the trip is included.'),
        ('❄️', 'AC', 'AC on for the whole journey, no extra charge.'),
        ('🛡️', 'Insurance &amp; permit', 'Commercial permit and insurance in place.'),
    ]), alt=True)
    + section('Popular from Pune', 'Where Pune <span class="hl">travels</span>', zones([
        ('Pilgrimage', 'Shirdi, Ashtavinayak, Pandharpur', 'Temple trips with early starts and same-day returns.'),
        ('Hill stations', 'Lonavala, Mahabaleshwar, Panchgani', 'Weekend getaways and family trips.'),
        ('Business', 'Mumbai, Nashik, Aurangabad', 'Meetings and plant visits, one-way or return.'),
        ('Long distance', 'Goa, Nagpur, Hyderabad', 'Multi-day trips with the same driver.'),
    ])),
    faqs=[
        ('What is the outstation cab rate from Pune?', 'A flat ₹12 per km with a 300 km minimum billing (₹3,600). Tolls are extra.'),
        ('Is there a one-way cab from Pune?', 'Yes. One-way drops are billed on the one-way distance, subject to the 300 km minimum.'),
        ('Are tolls and parking included?', 'No. Tolls and parking are paid separately as actuals. Fuel, driver and AC are included.'),
        ('Do you charge extra at night or on festivals?', 'No. The rate is the same 24×7, including festivals and long weekends.'),
        ('Which car do I get at ₹12/km?', 'Our standard sedan, usually a Swift Dzire, for up to 4 passengers. Larger vehicles are quoted on request.'),
    ],
    related=[('/routes.html', 'All Routes', 'Fares for 18 routes'), ('/pune-to-mumbai-airport/', 'Pune to Mumbai Airport', 'T1 and T2 transfers'),
             ('/car-rental-pune/', 'Car Rental in Pune', 'Local packages'), ('/verified-cab-service-pune.html', 'Verified Cab ₹1/km', 'Safety assurance')],
    cta=('Planning a trip out of Pune?', 'Send your route and date. We confirm the car, driver and fare in minutes.', 'Hi Baste Travels, I want to book an outstation cab from Pune'),
),
# 7 ─────────────────────────────────────────────────────────────────
dict(
    slug='fleet',
    crumb='Our Fleet',
    title='Fleet: Sedan, Innova Crysta, Tempo Traveller | Baste Travels',
    desc='Baste Travels fleet in Pune: Swift Dzire sedans, Ertiga and Innova Crysta SUVs, Honda City and Ciaz, and 12–17 seat Tempo Travellers, all with drivers.',
    keyword='cars available on rent in Pune',
    service=dict(name='Car and Tempo Traveller Rental with Driver', type='Vehicle rental with driver', catalog=True),
    body=lambda: f'''<section class="page-hero"><div class="container">
  <h1>Our <span class="hl">Fleet</span></h1>
  <p class="meta">Every vehicle comes with a verified driver, AC and commercial papers. Pick the size that fits your group and luggage.</p>
  <div class="hero-cta" style="justify-content:center;margin-top:20px">
    <a href="tel:{PHONE}" class="btn btn-primary btn-lg">📞 Call {PHONE_TXT}</a>
    <a href="{wa('Hi Baste Travels, I want to check vehicle availability')}" target="_blank" rel="noopener" class="btn btn-green btn-lg">💬 Check availability</a>
  </div>
</div></section>
<section><div class="container"><div class="lp-fleet">
''' + ''.join(f'''  <article class="lp-vehicle">
    <div class="lp-vehicle-art">{VEHICLE_SVG[kind].format(alt=alt)}</div>
    <div class="lp-vehicle-body">
      <h2>{name}</h2>
      <p class="lp-vehicle-models">{models}</p>
      <ul class="lp-specs"><li><strong>{seats}</strong> passengers</li><li><strong>{bags}</strong></li><li><strong>{rate}</strong></li></ul>
      <p>{best}</p>
      <a href="{wa(f'Hi Baste Travels, I want to book a {name}')}" target="_blank" rel="noopener" class="btn btn-green btn-sm">💬 Enquire for {name}</a>
    </div>
  </article>
''' for kind, alt, name, models, seats, bags, rate, best in [
        ('sedan', 'Side view illustration of a sedan car', 'Sedan', 'Swift Dzire', '4', 'Boot fits 2 large suitcases', '₹12/km outstation',
         'Our most booked car. Airport runs, business trips and outstation travel for up to four people.'),
        ('sedan', 'Side view illustration of a premium sedan', 'Premium Sedan', 'Honda City · Ciaz', '4', 'Roomy boot', 'Quoted on request',
         'Executive transport, client pickups and occasions when comfort and presentation matter.'),
        ('suv', 'Side view illustration of an SUV', 'SUV', 'Ertiga · Innova Crysta', '6–7', 'Space for family luggage', 'Quoted on request',
         'Families, small groups and long trips. Innova Crysta for the most comfortable ride on long highways.'),
        ('van', 'Side view illustration of a Tempo Traveller van', 'Tempo Traveller', '12 to 17 seat', '12–17', 'Rear luggage space', 'Quoted on request',
         'Group pilgrimages, weddings, corporate offsites and college trips.'),
    ]) + '''</div>
<p class="lp-fleet-note">Illustrations show the vehicle class. Exact model depends on availability; we confirm the car and registration number before your trip.</p>
</div></section>''' + section('Every vehicle', 'Standards across <span class="hl">the fleet</span>', features([
        ('📄', 'Commercial papers', 'Permit, insurance, fitness and PUC carried in the car.'),
        ('👮', 'Verified driver', 'Police verification and medical fitness on record.'),
        ('🧼', 'Cleaned before trips', 'Interior cleaned before every booking.'),
        ('❄️', 'Working AC', 'Checked before every trip.'),
    ]), alt=True) + article('''
<h2>Which vehicle should I book?</h2>
''' + table(['Group', 'Recommended', 'Why'], [
        ['1–3 people, light luggage', 'Sedan', 'Lowest fare, comfortable for city and highway'],
        ['4 people with suitcases', 'Sedan or SUV', 'Choose an SUV if everyone has a large bag'],
        ['Executive or client', 'Premium Sedan', 'More legroom and a quieter ride'],
        ['5–7 people', 'SUV (Ertiga / Innova Crysta)', 'Three rows of seats'],
        ['8–17 people', 'Tempo Traveller', 'One vehicle for the whole group'],
    ], 'Vehicle guide by group size.') + '''
<p>Not sure? Tell us how many people and bags, and where you are going. We will suggest the right vehicle. Book for <a href="/car-rental-pune/">local rental</a>, <a href="/pune-airport-taxi/">airport transfers</a>, <a href="/outstation-cab-service-pune/">outstation trips</a> or <a href="/monthly-car-rental-pune/">monthly rental</a>.</p>
'''),
    faqs=[
        ('Which car do I get for ₹12/km?', 'Our standard sedan, usually a Swift Dzire, for up to 4 passengers. Other vehicles are quoted on request.'),
        ('Can I choose a specific model?', 'You can request one and we will confirm it if available. We share the exact car and registration number before your trip.'),
        ('Do you have a Tempo Traveller in Pune?', 'Yes, 12 to 17 seat Tempo Travellers for groups, with a driver. Book early for weekends and wedding season.'),
        ('Are all vehicles commercially registered?', 'Yes. Every vehicle we send is commercially permitted and insured, with its documents in the car.'),
    ],
    related=[('/car-rental-pune/', 'Car Rental in Pune', 'Local 8 hr / 12 hr hire'), ('/outstation-cab-service-pune/', 'Outstation Cabs', '₹12/km across Maharashtra'),
             ('/monthly-car-rental-pune/', 'Monthly Car Rental', 'Dedicated car and driver'), ('/corporate-employee-transport/', 'Corporate Transport', 'Employee pickup and drop')],
    cta=('Found the right vehicle?', 'Call or WhatsApp to check availability for your date.', 'Hi Baste Travels, I want to check vehicle availability'),
),
]

# ─── Template assembly ──────────────────────────────────────────────

def load_template():
    src = (ROOT / 'contact.html').read_text(encoding='utf-8')
    head = src[:src.index('</head>')]
    top = src[src.index('<body>'):src.index('<section id="main"')]
    foot = src[src.index('<footer>'):]
    top = top.replace('<a href="/contact.html" class="active">Contact</a>', '<a href="/contact.html">Contact</a>')
    top = top.replace('<a href="/services.html">Services</a>', '<a href="/services.html" class="active">Services</a>', 1)
    return head, top, foot


def head_for(page, head):
    url = f"{SITE}/{page['slug']}/"
    title, desc = page['title'], page['desc']
    title_attr = html.unescape(title)
    head = re.sub(r'<title>.*?</title>', f'<title>{title}</title>', head)
    head = re.sub(r'(<meta (?:name="description"|property="og:description"|name="twitter:description") content=")[^"]*', lambda m: m.group(1) + desc, head)
    head = re.sub(r'(<meta (?:property="og:title"|name="twitter:title") content=")[^"]*', lambda m: m.group(1) + html.escape(title_attr, quote=True), head)
    head = re.sub(r'(<link rel="canonical" href=")[^"]*', lambda m: m.group(1) + url, head)
    head = re.sub(r'(<meta property="og:url" content=")[^"]*', lambda m: m.group(1) + url, head)
    return head + ''.join(f'<script type="application/ld+json">{json.dumps(ld, ensure_ascii=False, separators=(",", ":"))}</script>\n'
                          for ld in structured_data(page, url)) + '</head>\n'


def structured_data(page, url):
    crumbs = {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
        {"@type": "ListItem", "position": 1, "name": "Home", "item": f"{SITE}/"},
        {"@type": "ListItem", "position": 2, "name": "Services", "item": f"{SITE}/services.html"},
        {"@type": "ListItem", "position": 3, "name": page['crumb'], "item": url}]}
    s = page['service']
    service = {"@context": "https://schema.org", "@type": "Service", "name": s['name'], "serviceType": s['type'],
               "url": url, "description": html.unescape(page['desc']), "provider": {"@id": BIZ},
               "areaServed": [{"@type": "City", "name": "Pune"}, {"@type": "State", "name": "Maharashtra"}]}
    if s.get('price'):
        service['offers'] = {"@type": "Offer", "price": s['price'], "priceCurrency": "INR", "url": url,
                             "priceSpecification": {"@type": "UnitPriceSpecification", "price": "12", "priceCurrency": "INR", "unitText": "per km"}}
    elif s.get('unit_price'):
        service['offers'] = {"@type": "Offer", "priceCurrency": "INR", "url": url,
                             "priceSpecification": {"@type": "UnitPriceSpecification", "price": s['unit_price'], "priceCurrency": "INR", "unitText": "per km"}}
    if s.get('catalog'):
        service['hasOfferCatalog'] = {"@type": "OfferCatalog", "name": "Vehicles", "itemListElement": [
            {"@type": "Offer", "itemOffered": {"@type": "Service", "name": n}} for n in
            ['Sedan with driver (Swift Dzire)', 'Premium sedan with driver (Honda City, Ciaz)', 'SUV with driver (Ertiga, Innova Crysta)', 'Tempo Traveller with driver (12–17 seats)']]}
    faq = {"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [
        {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in page['faqs']]}
    return [crumbs, service, faq]


def build():
    head, top, foot = load_template()
    for page in PAGES:
        crumb = (f'<section id="main" class="breadcrumb"><div class="container"><ol><li><a href="/">Home</a></li><li class="sep">›</li>'
                 f'<li><a href="/services.html">Services</a></li><li class="sep">›</li><li class="current" aria-current="page">{page["crumb"]}</li></ol></div></section>\n')
        body = page['body']() + faq(page['faqs']) + related(page['related']) + cta(*page['cta'])
        out = head_for(page, head) + top + crumb + body + '\n' + foot
        dest = ROOT / page['slug'] / 'index.html'
        dest.parent.mkdir(exist_ok=True)
        dest.write_text(out, encoding='utf-8')
        print(f"built /{page['slug']}/  ({page['keyword']})")


if __name__ == '__main__':
    build()
