// Plain-language labels and formatting shared by all views (see docs/design-system.md → Copy)

// Okabe–Ito colour-blind-safe set, in campaign rank order
const CAMPAIGN_COLORS = ['#0072B2', '#D55E00', '#009E73', '#CC79A7', '#E69F00', '#56B4E9', '#8C564B']
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
  co_link: 'Same link',
  co_reply: 'Replies to the same post',
  co_retweet: 'Same retweet',
}

export const THREATS = {
  incitement: 'Incitement',
  targeted_harassment: 'Targeted harassment',
  organized_misinformation: 'Organised misinformation',
  benign_coordination: 'Benign coordination',
}

export const fmt = (n) => (n ?? 0).toLocaleString('en-US')

export const fmtTime = (t, withYear = false) =>
  new Date(t * 1000).toLocaleString('en-GB', {
    day: 'numeric', month: 'short', ...(withYear && { year: 'numeric' }), hour: '2-digit', minute: '2-digit',
  })

export const fmtDuration = (seconds) => {
  const s = Math.max(0, Math.round(seconds))
  return s < 60 ? `${s} s` : `${Math.floor(s / 60)} min ${s % 60} s`
}

export const BUCKET_LABEL = { 60: 'minute', 300: '5 minutes', 900: '15 minutes', 3600: 'hour', 21600: '6 hours', 86400: 'day', 604800: 'week' }
