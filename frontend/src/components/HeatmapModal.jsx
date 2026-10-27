import { X, Image as ImageIcon } from 'lucide-react';
import { getHeatmapUrl } from '../api';

/**
 * Modal to display the ELA tamper detection heatmap for a document.
 *
 * @param {number} documentId - Document ID (used to build heatmap URL)
 * @param {string} filename - Original document filename
 * @param {Function} onClose - Close callback
 */
export default function HeatmapModal({ documentId, filename, onClose }) {
  const heatmapUrl = getHeatmapUrl(documentId);

  return (
    <div
      className="fixed inset-0 bg-black/60 z-50 flex items-center justify-center p-4"
      onClick={onClose}
    >
      <div
        className="bg-white rounded-xl shadow-2xl max-w-2xl w-full max-h-[90vh] overflow-y-auto"
        onClick={e => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-gray-200">
          <div className="flex items-center gap-2">
            <ImageIcon size={20} className="text-purple-600" />
            <h3 className="text-base font-semibold text-gray-900">
              Error Level Analysis Heatmap
            </h3>
          </div>
          <button onClick={onClose} className="p-1 hover:bg-gray-100 rounded-lg">
            <X size={18} className="text-gray-500" />
          </button>
        </div>

        {/* Content */}
        <div className="p-4 space-y-4">
          <div className="bg-gray-50 rounded-lg p-3 text-sm text-gray-600">
            <p className="font-medium text-gray-800 truncate">{filename}</p>
            <p className="text-xs text-gray-400 mt-0.5">
              Brighter regions indicate higher error levels — possible edited areas.
            </p>
          </div>

          {/* Heatmap image */}
          <div className="bg-gray-900 rounded-lg overflow-hidden flex items-center justify-center min-h-[200px]">
            <img
              src={heatmapUrl}
              alt="ELA tamper detection heatmap"
              className="max-w-full max-h-[500px] object-contain"
              onError={e => {
                e.target.style.display = 'none';
                e.target.nextSibling.style.display = 'block';
              }}
            />
            <div style={{ display: 'none' }} className="text-center text-gray-400 py-12">
              <ImageIcon size={40} className="mx-auto mb-2 opacity-30" />
              <p className="text-sm">Heatmap image not available</p>
              <p className="text-xs mt-1 text-gray-500">The document may not have been processed yet</p>
            </div>
          </div>

          {/* Legend */}
          <div className="flex items-center gap-6 text-xs text-gray-500 px-1">
            <span className="font-medium text-gray-700">ELA Legend:</span>
            <div className="flex items-center gap-1.5">
              <div className="w-3 h-3 rounded bg-black border border-gray-300" />
              <span>Uniform (authentic)</span>
            </div>
            <div className="flex items-center gap-1.5">
              <div className="w-3 h-3 rounded bg-amber-400" />
              <span>Moderate anomaly</span>
            </div>
            <div className="flex items-center gap-1.5">
              <div className="w-3 h-3 rounded bg-white border border-gray-300" />
              <span>High anomaly (possible edit)</span>
            </div>
          </div>

          <p className="text-xs text-gray-400 italic">
            ⚠ ELA is a heuristic. Heavily compressed or re-saved images may produce
            false positives. This is one signal among several.
          </p>
        </div>

        <div className="flex justify-end p-4 border-t border-gray-100">
          <button
            onClick={onClose}
            className="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
}
