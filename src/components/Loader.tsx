import React from 'react';

export default function Loader() {
  return (
    <div className="flex space-x-2">
      <div className="w-2 h-2 bg-robin-green rounded-full animate-bounce [animation-delay:-0.3s]"></div>
      <div className="w-2 h-2 bg-robin-green rounded-full animate-bounce [animation-delay:-0.15s]"></div>
      <div className="w-2 h-2 bg-robin-green rounded-full animate-bounce"></div>
    </div>
  );
}
