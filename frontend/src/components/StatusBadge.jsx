/**
 * Reusable status badge component for displaying color-coded labels.
 * Maps common status strings to appropriate color schemes.
 *
 * @param {string} status - Status text to display
 * @param {string} [size='sm'] - Badge size: 'sm' | 'md'
 * @param {string} [colorOverride] - Override automatic color: 'green' | 'amber' | 'red' | 'blue' | 'gray'
 */
export default function StatusBadge({ status, size = 'sm', colorOverride }) {
  if (!status) return null;

  // Map common status values to colors
  const getColor = () => {
    if (colorOverride) return colorOverride;

    const normalized = String(status).toLowerCase().replace(/[_\s-]/g, '');

    const greenStatuses = [
      'compliant', 'match', 'pass', 'passed', 'approved', 'verified',
      'fasttrack', 'valid', 'complete', 'completed', 'success', 'processed',
    ];
    const amberStatuses = [
      'partialmatch', 'partial', 'warning', 'pending', 'pendingreview',
      'standard', 'review', 'raisedeficiency', 'deficiency', 'submitted',
    ];
    const redStatuses = [
      'noncompliant', 'mismatch', 'fail', 'failed', 'rejected', 'flagged',
      'seniorreview', 'tampered', 'invalid', 'critical',
    ];

    if (greenStatuses.includes(normalized)) return 'green';
    if (amberStatuses.includes(normalized)) return 'amber';
    if (redStatuses.includes(normalized)) return 'red';
    return 'gray';
  };

  const color = getColor();

  const colorClasses = {
    green: 'bg-success-100 text-success-700 ring-success-500/20',
    amber: 'bg-warning-100 text-warning-700 ring-warning-500/20',
    red: 'bg-danger-100 text-danger-700 ring-danger-500/20',
    blue: 'bg-primary-100 text-primary-700 ring-primary-500/20',
    gray: 'bg-gray-100 text-gray-700 ring-gray-500/20',
  };

  const sizeClasses = {
    sm: 'px-2 py-0.5 text-xs',
    md: 'px-3 py-1 text-sm',
  };

  // Format display text: snake_case -> Title Case
  const displayText = String(status)
    .replace(/_/g, ' ')
    .replace(/\b\w/g, (c) => c.toUpperCase());

  return (
    <span
      className={`
        inline-flex items-center font-semibold rounded-full ring-1 ring-inset
        ${colorClasses[color]} ${sizeClasses[size]}
      `}
    >
      {displayText}
    </span>
  );
}
