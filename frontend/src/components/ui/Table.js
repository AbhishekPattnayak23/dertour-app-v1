import "../styles/designTokens.css";
import React from 'react';

const Table = ({
  columns,
  data,
  className = '',
  striped = false,
  hoverable = false
}) => {
  const baseClasses = 'min-w-full divide-y divide-gray-200';
  const stripedClasses = striped ? 'divide-y divide-gray-200' : '';
  const hoverClasses = hoverable ? 'hover:bg-gray-50' : '';

  return (
    <div className="overflow-x-auto">
      <table className={`${baseClasses} ${className}`}>
        <thead className="bg-gray-50">
          <tr>
            {columns.map((column, index) => (
              <th
                key={index}
                className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"
              >
                {column.header}
              </th>
            ))}
          </tr>
        </thead>
        <tbody className={`bg-white ${stripedClasses}`}>
          {data.map((row, rowIndex) => (
            <tr key={rowIndex} className={hoverClasses}>
              {columns.map((column, colIndex) => (
                <td key={colIndex} className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                  {column.accessor ? row[column.accessor] : column.cell ? column.cell(row) : ''}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

export default Table;
