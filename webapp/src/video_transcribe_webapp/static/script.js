document.addEventListener('DOMContentLoaded', function() {
    const uploadArea = document.getElementById('uploadArea');
    const fileInput = document.getElementById('fileInput');
    const browseLink = document.getElementById('browseLink');
    const statusArea = document.getElementById('statusArea');
    const statusMessage = document.getElementById('statusMessage');

    // Supported video file types
    const supportedTypes = ['video/mp4', 'video/avi', 'video/quicktime', 'video/x-msvideo', 
                           'video/x-matroska', 'video/x-ms-wmv', 'video/x-flv', 
                           'video/webm', 'video/x-m4v', 'video/3gpp'];

    function isVideoFile(file) {
        return supportedTypes.includes(file.type) || 
               /\.(mp4|avi|mov|mkv|wmv|flv|webm|m4v|3gp)$/i.test(file.name);
    }

    function showStatus(message, type) {
        statusMessage.textContent = message;
        statusArea.className = `status-area ${type}`;
        statusArea.style.display = 'block';
    }

    function hideStatus() {
        statusArea.style.display = 'none';
    }

    function uploadFile(file) {
        if (!isVideoFile(file)) {
            showStatus('Error: Only video files are supported.', 'error');
            return;
        }

        const formData = new FormData();
        formData.append('file', file);

        showStatus(`Uploading ${file.name}...`, 'uploading');

        fetch('/upload', {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                showStatus(data.message, 'success');
            } else {
                showStatus(data.error || 'Upload failed', 'error');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            showStatus('Upload failed: Network error', 'error');
        });
    }

    // Click to browse files
    browseLink.addEventListener('click', function(e) {
        e.stopPropagation();
        fileInput.click();
    });

    uploadArea.addEventListener('click', function() {
        fileInput.click();
    });

    // File input change handler
    fileInput.addEventListener('change', function(e) {
        const files = e.target.files;
        if (files.length > 0) {
            uploadFile(files[0]);
        }
    });

    // Drag and drop handlers
    uploadArea.addEventListener('dragenter', function(e) {
        e.preventDefault();
        uploadArea.classList.add('dragover');
    });

    uploadArea.addEventListener('dragover', function(e) {
        e.preventDefault();
        uploadArea.classList.add('dragover');
    });

    uploadArea.addEventListener('dragleave', function(e) {
        e.preventDefault();
        if (!uploadArea.contains(e.relatedTarget)) {
            uploadArea.classList.remove('dragover');
        }
    });

    uploadArea.addEventListener('drop', function(e) {
        e.preventDefault();
        uploadArea.classList.remove('dragover');
        
        const files = e.dataTransfer.files;
        if (files.length > 0) {
            uploadFile(files[0]);
        }
    });

    // Prevent default drag behaviors on the document
    document.addEventListener('dragenter', function(e) {
        e.preventDefault();
    });

    document.addEventListener('dragover', function(e) {
        e.preventDefault();
    });

    document.addEventListener('drop', function(e) {
        e.preventDefault();
    });
});