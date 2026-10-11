// Relative by default: CRA's dev-server "proxy" field (package.json) forwards
// /api/* to Flask locally, and same-origin routing handles it in production.
export const API_BASE = process.env.REACT_APP_API_BASE_URL || '';