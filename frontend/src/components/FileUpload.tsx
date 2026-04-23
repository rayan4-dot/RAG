import React, { useState, useRef } from 'react';
import { UploadCloud, File, CheckCircle } from 'lucide-react';
import './FileUpload.css';

interface FileUploadProps {
  onUploadSuccess: (chunksProcessed: number) => void;
}

export function FileUpload({ onUploadSuccess }: FileUploadProps) {
  const [isDragging, setIsDragging] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = () => {
    setIsDragging(false);
  };

  const processFile = async (file: File) => {
    if (file.type !== 'application/pdf') {
      setError('Please upload a valid PDF file.');
      return;
    }
    
    setError(null);
    setSuccessMsg(null);
    setIsUploading(true);

    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await fetch('/api/upload', {
        method: 'POST',
        body: formData,
      });
      
      const data = await response.json();
      
      if (!response.ok) {
        throw new Error(data.detail || 'Upload failed');
      }
      
      setSuccessMsg(`Processed ${data.chunks_processed} chunks successfully!`);
      onUploadSuccess(data.chunks_processed);
    } catch (err: any) {
      setError(err.message || 'An error occurred during upload.');
    } finally {
      setIsUploading(false);
      setIsDragging(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      processFile(e.dataTransfer.files[0]);
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      processFile(e.target.files[0]);
    }
  };

  return (
    <div className="upload-container glass-panel animate-fade-in">
      <h3>Knowledge Base Builder</h3>
      <p className="subtitle">Upload PDFs to augment the AI's knowledge before chatting.</p>
      
      <div 
        className={`drop-zone ${isDragging ? 'dragging' : ''} ${isUploading ? 'uploading' : ''}`}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onClick={() => fileInputRef.current?.click()}
      >
        <input 
          type="file" 
          accept=".pdf" 
          ref={fileInputRef} 
          onChange={handleFileChange} 
          style={{ display: 'none' }} 
        />
        
        {isUploading ? (
          <div className="upload-state animate-pulse">
            <UploadCloud size={48} className="icon-primary" />
            <p>Processing document and generating embeddings...</p>
          </div>
        ) : successMsg ? (
          <div className="upload-state success">
            <CheckCircle size={48} className="icon-success" />
            <p className="success-text">{successMsg}</p>
            <span className="upload-hint">Click or drag another file</span>
          </div>
        ) : (
          <div className="upload-state">
            <File size={48} className="icon-secondary" />
            <p><strong>Click to upload</strong> or drag and drop</p>
            <span className="upload-hint">PDF files only (max 10MB)</span>
          </div>
        )}
      </div>
      
      {error && <div className="error-msg animate-fade-in">{error}</div>}
    </div>
  );
}
