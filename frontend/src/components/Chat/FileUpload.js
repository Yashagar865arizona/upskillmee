import React, { useState, useRef, useCallback } from 'react';
import styles from './FileUpload.module.css';

const FileUpload = ({ 
  onFileUpload, 
  onClose, 
  maxFileSize = 10 * 1024 * 1024, // 10MB
  acceptedTypes = ['image/*', 'text/*', '.pdf', '.doc', '.docx', '.txt', '.md']
}) => {
  const [dragActive, setDragActive] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [error, setError] = useState(null);
  const fileInputRef = useRef(null);

  const validateFile = (file) => {
    if (file.size > maxFileSize) {
      throw new Error(`File size must be less than ${Math.round(maxFileSize / 1024 / 1024)}MB`);
    }

    const fileType = file.type;
    const fileName = file.name.toLowerCase();
    
    const isValidType = acceptedTypes.some(type => {
      if (type.startsWith('.')) {
        return fileName.endsWith(type);
      }
      if (type.includes('*')) {
        const baseType = type.split('/')[0];
        return fileType.startsWith(baseType);
      }
      return fileType === type;
    });

    if (!isValidType) {
      throw new Error('File type not supported');
    }
  };

  const handleFiles = useCallback(async (files) => {
    const fileArray = Array.from(files);
    setError(null);
    setUploading(true);
    setUploadProgress(0);

    try {
      const uploadedFiles = [];
      const totalFiles = fileArray.length;
      
      for (let i = 0; i < fileArray.length; i++) {
        const file = fileArray[i];
        validateFile(file);
        
        // Smooth progress animation
        const baseProgress = (i / totalFiles) * 100;
        const fileProgress = 100 / totalFiles;
        
        const progressInterval = setInterval(() => {
          setUploadProgress(prev => {
            const targetProgress = baseProgress + (fileProgress * 0.9);
            const increment = Math.random() * 5 + 2;
            const newProgress = Math.min(prev + increment, targetProgress);
            return newProgress;
          });
        }, 50);

        // Create file preview
        const fileData = {
          id: Date.now() + i,
          name: file.name,
          size: file.size,
          type: file.type,
          file: file,
          preview: null
        };

        // Generate preview for images
        if (file.type.startsWith('image/')) {
          fileData.preview = await createImagePreview(file);
        }

        // Read file content for text files
        if (file.type.startsWith('text/') || file.name.endsWith('.md') || file.name.endsWith('.txt')) {
          fileData.content = await readTextFile(file);
        }

        clearInterval(progressInterval);
        setUploadProgress(baseProgress + fileProgress);
        uploadedFiles.push(fileData);
        
        // Small delay for better UX
        await new Promise(resolve => setTimeout(resolve, 200));
      }

      // Complete progress
      setUploadProgress(100);
      await new Promise(resolve => setTimeout(resolve, 300));

      await onFileUpload(uploadedFiles);
      setUploading(false);
      setUploadProgress(0);
      onClose();
    } catch (err) {
      setError(err.message);
      setUploading(false);
      setUploadProgress(0);
    }
  }, [onFileUpload, onClose, maxFileSize, acceptedTypes]);

  const createImagePreview = (file) => {
    return new Promise((resolve) => {
      const reader = new FileReader();
      reader.onload = (e) => resolve(e.target.result);
      reader.readAsDataURL(file);
    });
  };

  const readTextFile = (file) => {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.onload = (e) => resolve(e.target.result);
      reader.onerror = () => reject(new Error('Failed to read file'));
      reader.readAsText(file);
    });
  };

  const handleDrag = useCallback((e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  }, []);

  const handleDrop = useCallback((e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFiles(e.dataTransfer.files);
    }
  }, [handleFiles]);

  const handleFileSelect = (e) => {
    if (e.target.files && e.target.files[0]) {
      handleFiles(e.target.files);
    }
  };

  const formatFileSize = (bytes) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  return (
    <div className={styles.overlay} onClick={onClose}>
      <div className={styles.modal} onClick={(e) => e.stopPropagation()}>
        <div className={styles.header}>
          <h3>Upload Files</h3>
          <button className={styles.closeBtn} onClick={onClose}>
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M18 6L6 18M6 6l12 12"/>
            </svg>
          </button>
        </div>

        <div className={styles.content}>
          {error && (
            <div className={styles.error}>
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <circle cx="12" cy="12" r="10"/>
                <path d="M15 9l-6 6M9 9l6 6"/>
              </svg>
              {error}
            </div>
          )}

          <div
            className={`${styles.dropzone} ${dragActive ? styles.active : ''} ${uploading ? styles.uploading : ''}`}
            onDragEnter={handleDrag}
            onDragLeave={handleDrag}
            onDragOver={handleDrag}
            onDrop={handleDrop}
            onClick={() => fileInputRef.current?.click()}
          >
            <input
              ref={fileInputRef}
              type="file"
              multiple
              accept={acceptedTypes.join(',')}
              onChange={handleFileSelect}
              style={{ display: 'none' }}
            />

            {uploading ? (
              <div className={styles.uploadingState}>
                <div className={styles.progressBar}>
                  <div 
                    className={styles.progressFill} 
                    style={{ width: `${uploadProgress}%` }}
                  />
                </div>
                <p>Uploading... {Math.round(uploadProgress)}%</p>
              </div>
            ) : (
              <div className={styles.dropzoneContent}>
                <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1">
                  <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
                  <polyline points="14,2 14,8 20,8"/>
                  <line x1="16" y1="13" x2="8" y2="13"/>
                  <line x1="16" y1="17" x2="8" y2="17"/>
                  <polyline points="10,9 9,9 8,9"/>
                </svg>
                <h4>Drop files here or click to browse</h4>
                <p>
                  Supported formats: Images, Text files, PDFs, Documents
                  <br />
                  Maximum size: {Math.round(maxFileSize / 1024 / 1024)}MB per file
                </p>
              </div>
            )}
          </div>

          <div className={styles.supportedFormats}>
            <h5>Supported file types:</h5>
            <div className={styles.formatTags}>
              <span className={styles.formatTag}>Images (JPG, PNG, GIF)</span>
              <span className={styles.formatTag}>Documents (PDF, DOC, DOCX)</span>
              <span className={styles.formatTag}>Text (TXT, MD)</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default FileUpload;