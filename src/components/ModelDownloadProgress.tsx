import React, { useEffect, useState } from 'react';

export default function ModelDownloadProgress() {
  return (
    <div className="bg-card border border-card-border rounded-2xl p-6 mb-6 animate-fade-in">
      <div className="flex items-center gap-4">
        <div className="flex-shrink-0">
          <svg className="animate-spin h-6 w-6 text-robin-green" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
          </svg>
        </div>
        <div>
          <h3 className="text-lg font-medium text-white">Downloading Model</h3>
          <p className="text-robin-gray-400">Please wait while we download the Llama 3 model...</p>
        </div>
      </div>
      <div className="mt-4">
        <div className="h-2 bg-robin-black rounded-full">
          <div className="h-2 bg-robin-green rounded-full animate-pulse" style={{ width: '60%' }}></div>
        </div>
      </div>
    </div>
  );
} 
