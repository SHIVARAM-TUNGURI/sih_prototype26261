/**
 * Reusable score card component.
 * Displays a metric with a label, value, and color coding based on thresholds.
 *
 * @param {string} label - Display label for the metric
 * @param {number|string} value - The score value to display
 * @param {string} [color] - Override color ('green', 'amber', 'red', 'blue')
 * @param {number} [maxValue=100] - Maximum value for percentage-based coloring
 * @param {React.ElementType} [icon] - Optional lucide-react icon component
 * @param {string} [subtitle] - Optional subtitle text
 * @param {boolean} [isPercentage=false] - Whether to show value as percentage
 */
export default function ScoreCard({
  label,
  value,
  color,
  maxValue = 100,
  icon: Icon,
  subtitle,
  isPercentage = false,
}) {
  // Auto-determine color from value if not explicitly provided
  const getAutoColor = () => {
    if (color) return color;
    const numVal = typeof value === 'number' ? value : parseFloat(value);
    if (isNaN(numVal)) return 'blue';
    const pct = (numVal / maxValue) * 100;
    if (pct >= 70) return 'green';
    if (pct >= 40) return 'amber';
    return 'red';
  };

  const resolvedColor = getAutoColor();

  const colorClasses = {
    green: {
      bg: 'bg-success-50',
      border: 'border-success-500',
      text: 'text-success-700',
      iconBg: 'bg-success-100',
    },
    amber: {
      bg: 'bg-warning-50',
      border: 'border-warning-500',
      text: 'text-warning-700',
      iconBg: 'bg-warning-100',
    },
    red: {
      bg: 'bg-danger-50',
      border: 'border-danger-500',
      text: 'text-danger-700',
      iconBg: 'bg-danger-100',
    },
    blue: {
      bg: 'bg-primary-50',
      border: 'border-primary-500',
      text: 'text-primary-700',
      iconBg: 'bg-primary-100',
    },
  };

  const classes = colorClasses[resolvedColor] || colorClasses.blue;

  const displayValue = value != null
    ? (isPercentage ? `${(typeof value === 'number' ? value : parseFloat(value) || 0).toFixed(1)}%` : value)
    : '—';

  return (
    <div className={`${classes.bg} border-l-4 ${classes.border} rounded-lg p-4 flex items-center gap-4`}>
      {Icon && (
        <div className={`${classes.iconBg} p-3 rounded-full`}>
          <Icon className={`w-6 h-6 ${classes.text}`} />
        </div>
      )}
      <div className="flex-1 min-w-0">
        <p className="text-xs font-medium text-gray-500 uppercase tracking-wider">{label}</p>
        <p className={`text-2xl font-bold ${classes.text} mt-0.5`}>{displayValue}</p>
        {subtitle && (
          <p className="text-xs text-gray-500 mt-0.5">{subtitle}</p>
        )}
      </div>
    </div>
  );
}
