/**
 * Format a date for display
 * @param {string|Date} dateString - The date to format
 * @returns {string} Formatted date string
 */
export const formatDate = (dateString) => {
  if (!dateString) return "N/A";
  
  const date = new Date(dateString);
  
  if (isNaN(date.getTime())) {
    return "Invalid date";
  }
  
  return new Intl.DateTimeFormat("en-US", {
    year: "numeric",
    month: "long",
    day: "numeric",
  }).format(date);
};

/**
 * Calculate days remaining until a date
 * @param {string|Date} endDate - The end date
 * @returns {number} Days remaining (0 if date is past)
 */
export const getDaysRemaining = (endDate) => {
  if (!endDate) return 0;

  const end = new Date(endDate);
  const now = new Date();
  
  if (isNaN(end.getTime())) {
    return 0;
  }
  
  // Get difference in days
  const diffTime = end - now;
  const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));

  return diffDays > 0 ? diffDays : 0;
};

/**
 * Check if a date is in the past
 * @param {string|Date} dateString - The date to check
 * @returns {boolean} True if date is in the past
 */
export const isDatePast = (dateString) => {
  if (!dateString) return true;
  
  const date = new Date(dateString);
  const now = new Date();
  
  if (isNaN(date.getTime())) {
    return true;
  }
  
  return date < now;
};
