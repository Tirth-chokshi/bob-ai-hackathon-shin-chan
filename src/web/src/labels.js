// Plain-language labels and formatting shared by all views (see docs/design-system.md → Copy)

// Okabe–Ito colour-blind-safe set in campaign rank order, then three more distinct hues
const CAMPAIGN_COLORS = ['#0072B2', '#D55E00', '#009E73', '#CC79A7', '#E69F00', '#56B4E9', '#8C564B', '#7B3FA0', '#17A2B8', '#9A9A2E']
export const campaignColor = (id) => CAMPAIGN_COLORS[Number(String(id).slice(1)) - 1] ?? '#7F7F7F'

export const FEATURES = {
  speed: { label: 'Posted within seconds of each other', max: 25 },
  duplication: { label: 'Near-identical text', max: 25 },
  multi_signal: { label: 'Several coordination signals', max: 15 },
  fresh_accounts: { label: 'Newly created accounts', max: 15 },
  burst: { label: 'Sudden burst of activity', max: 10 },
  concentration: { label: 'Same hashtag or link', max: 10 },
}

export const SIGNALS = {
  co_tweet: 'Same text',
  co_similar_tweet: 'Similar text',
  co_link: 'Same link or video',
  co_reply: 'Replies to the same post',
  co_retweet: 'Same retweet',
}

export const THREATS = {
  incitement: 'Incitement',
  targeted_harassment: 'Targeted harassment',
  organized_misinformation: 'Organised misinformation',
  benign_coordination: 'Benign coordination',
}

// Neutral text chips instead of brand logos
export const PLATFORMS = {
  whatsapp: { short: 'WA', label: 'WhatsApp' },
  x: { short: 'X', label: 'X (Twitter)' },
  facebook: { short: 'FB', label: 'Facebook' },
  telegram: { short: 'TG', label: 'Telegram' },
  instagram: { short: 'IG', label: 'Instagram' },
  youtube: { short: 'YT', label: 'YouTube' },
}
export const platformLabel = (p) => PLATFORMS[p] ?? { short: String(p).slice(0, 3).toUpperCase(), label: p }

// Short labels for the most common languages here; any other code gets its English name from the browser
const LANGUAGES = { hi: 'हिंदी', hinglish: 'Hinglish', en: 'English' }
let languageNames
try { languageNames = new Intl.DisplayNames(['en'], { type: 'language' }) } catch (_) {}
export const langLabel = (code) => {
  if (LANGUAGES[code]) return LANGUAGES[code]
  if (String(code).length > 3) return code.charAt(0).toUpperCase() + code.slice(1)  // a name from the file, e.g. "farsi (persian)"
  try { return languageNames?.of(code) ?? code } catch (_) { return code }
}

export const fmt = (n) => (n ?? 0).toLocaleString('en-US')

// Times are shown in the dataset's own clock (IST for the Indian incidents, UTC for research archives), whatever
// the viewer's computer says. App sets it when the dataset changes.
let zone = 'Asia/Kolkata'
export const setDisplayZone = (z) => { zone = z || 'Asia/Kolkata' }
export const getDisplayZone = () => zone
export const zoneLabel = () => (zone === 'Asia/Kolkata' ? 'IST' : zone === 'UTC' ? 'UTC' : zone)

export const fmtTime = (t, withYear = false) =>
  new Date(t * 1000).toLocaleString('en-GB', {
    day: 'numeric', month: 'short', ...(withYear && { year: 'numeric' }), hour: '2-digit', minute: '2-digit',
    timeZone: zone,
  })

export const fmtClock = (t) =>
  new Date(t * 1000).toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit', timeZone: zone })

export const fmtDay = (t) =>
  new Date(t * 1000).toLocaleDateString('en-GB', { weekday: 'short', day: 'numeric', month: 'short', timeZone: zone })

export const fmtDate = (t, withYear = true) =>
  new Date(t * 1000).toLocaleDateString('en-GB', { day: 'numeric', month: 'short', ...(withYear && { year: 'numeric' }), timeZone: zone })

// Clock time alone within one day of data, otherwise with the date: "14:04" or "3 Jan 16:48"
export const fmtWhen = (t, span) => (span > 20 * 3600 ? `${fmtDate(t, span > 300 * 86400)} ${fmtClock(t)}` : fmtClock(t))

// Seconds east of UTC in the display zone at time t (for lining buckets and ticks up with local hours and days)
export const zoneOffset = (t) => {
  const parts = Object.fromEntries(new Intl.DateTimeFormat('en-US', {
    timeZone: zone, hourCycle: 'h23', year: 'numeric', month: 'numeric', day: 'numeric', hour: 'numeric', minute: 'numeric', second: 'numeric',
  }).formatToParts(new Date(t * 1000)).map((x) => [x.type, x.value]))
  return (Date.UTC(parts.year, parts.month - 1, parts.day, parts.hour, parts.minute, parts.second) / 1000) - Math.floor(t)
}

export const fmtDuration = (seconds) => {
  const s = Math.max(0, Math.round(seconds))
  return s < 60 ? `${s} s` : `${Math.floor(s / 60)} min ${s % 60} s`
}

// A gap like "12 min", "3 h 35 m" or "10 days"
export const fmtGap = (seconds) => {
  const m = Math.max(0, Math.round(seconds / 60))
  if (m < 60) return `${m} min`
  if (m < 48 * 60) return `${Math.floor(m / 60)} h ${m % 60} m`
  const d = Math.round(m / 1440)
  return `${d} days`
}

// Bucket sizes a person would pick; the timeline only ever uses these
export const NICE_BUCKETS = [60, 300, 900, 1800, 3600, 3 * 3600, 6 * 3600, 12 * 3600, 86400, 7 * 86400, 30 * 86400]
export const BUCKET_LABEL = {
  60: 'minute', 300: '5 minutes', 900: '15 minutes', 1800: '30 minutes', 3600: 'hour', 10800: '3 hours',
  21600: '6 hours', 43200: '12 hours', 86400: 'day', 604800: 'week', 2592000: '30 days',
}

// "22 Sep 2020, 10:02–15:05" within a day, else "1 Nov – 29 Dec 2015"
export const fmtRange = (a, b) => {
  const sameDay = fmtDate(a) === fmtDate(b)
  if (sameDay) return `${fmtDate(a)}, ${fmtClock(a)}–${fmtClock(b)} ${zoneLabel()}`
  const sameYear = fmtDate(a).slice(-4) === fmtDate(b).slice(-4)
  return `${fmtDate(a, !sameYear)} – ${fmtDate(b)}`
}
