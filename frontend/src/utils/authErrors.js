/**
 * Converts Axios / Django REST Framework errors into short user-facing messages.
 * Never returns stack traces, SQL, or secret material.
 */
export const extractErrorMessage = (err, defaultMsg = 'An unexpected error occurred.') => {
  if (!err) return defaultMsg;

  if (!err.response) {
    if (err.message === 'Network Error' || err.code === 'ERR_NETWORK') {
      return 'Unable to connect to the KrishiSetu API. The backend may be waking up (about 40 seconds on free hosting) or the frontend may be calling the wrong API URL. Please retry in a moment.';
    }
    if (err.code === 'ECONNABORTED' || err.message?.toLowerCase().includes('timeout')) {
      return 'Connection timed out waiting for the backend. If the API was asleep, wait a few seconds and try again.';
    }
    return err.message || defaultMsg;
  }

  const { data, status } = err.response;

  if (status === 401) {
    if (typeof data?.detail === 'string') {
      return data.detail === 'No active account found with the given credentials'
        ? 'Invalid email or password.'
        : data.detail;
    }
    return 'Invalid email or password.';
  }

  if (status >= 500) {
    return `Server error (${status}). The backend encountered an unexpected error. Please try again shortly.`;
  }

  if (typeof data === 'string') {
    if (data.trim().startsWith('<')) {
      return `Server error (${status}). Please try again shortly.`;
    }
    return data || defaultMsg;
  }

  if (data && typeof data === 'object') {
    if (typeof data.detail === 'string') {
      return data.detail;
    }
    if (typeof data.message === 'string') {
      return data.message;
    }
    if (Array.isArray(data.non_field_errors) && data.non_field_errors.length > 0) {
      return data.non_field_errors[0];
    }
    if (Array.isArray(data) && data.length > 0 && typeof data[0] === 'string') {
      return data[0];
    }

    const fieldLabels = {
      email: 'Email',
      phone: 'Phone number',
      password: 'Password',
      password_confirm: 'Confirm password',
      full_name: 'Full name',
      role: 'Role',
      village: 'Village',
      district: 'District',
      business_name: 'Business name',
    };

    const keys = Object.keys(data);
    if (keys.length > 0) {
      const firstKey = keys[0];
      const val = data[firstKey];
      const fieldLabel = fieldLabels[firstKey] || firstKey
        .replace(/_/g, ' ')
        .replace(/\b\w/g, (char) => char.toUpperCase());

      if (Array.isArray(val) && val.length > 0) {
        return `${fieldLabel}: ${val[0]}`;
      }
      if (typeof val === 'string') {
        return `${fieldLabel}: ${val}`;
      }
      if (typeof val === 'object' && val !== null) {
        const subKeys = Object.keys(val);
        if (subKeys.length > 0) {
          const subVal = val[subKeys[0]];
          if (Array.isArray(subVal) && subVal.length > 0) {
            return `${fieldLabel} (${subKeys[0]}): ${subVal[0]}`;
          }
          if (typeof subVal === 'string') {
            return `${fieldLabel} (${subKeys[0]}): ${subVal}`;
          }
        }
      }
    }
  }

  return defaultMsg;
};
