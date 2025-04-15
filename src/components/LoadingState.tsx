import React from 'react';

export default function LoadingState() {
  return (
    <div className="flex items-center justify-center p-8">
      <div className="flex items-center gap-4">
        <div className="w-3 h-3 bg-[#00ff9d] rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
        <div className="w-3 h-3 bg-[#00ff9d] rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
        <div className="w-3 h-3 bg-[#00ff9d] rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
      </div>
    </div>
  );
} 
