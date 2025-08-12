document.addEventListener('DOMContentLoaded', function() {
    const uploadArea = document.getElementById('uploadArea');
    const fileInput = document.getElementById('fileInput');
    const browseLink = document.getElementById('browseLink');
    const statusArea = document.getElementById('statusArea');
    const statusMessage = document.getElementById('statusMessage');
    const progressBar = document.getElementById('progressBar');
    const progressFill = document.getElementById('progressFill');
    const resultsArea = document.getElementById('resultsArea');
    const summaryContent = document.getElementById('summaryContent');
    const transcriptContent = document.getElementById('transcriptContent');
    const speakerName = document.getElementById('speakerName');

    // Supported video and audio file types
    const supportedTypes = ['video/mp4', 'video/avi', 'video/quicktime', 'video/x-msvideo', 
                           'video/x-matroska', 'video/x-ms-wmv', 'video/x-flv', 
                           'video/webm', 'video/x-m4v', 'video/3gpp',
                           'audio/wav', 'audio/mpeg', 'audio/mp3', 'audio/flac', 'audio/ogg'];

    function isValidFile(file) {
        return supportedTypes.includes(file.type) || 
               /\.(mp4|avi|mov|mkv|wmv|flv|webm|m4v|3gp|wav|mp3|flac|ogg)$/i.test(file.name);
    }

    function showStatus(message, type) {
        statusMessage.textContent = message;
        statusArea.className = `status-area ${type}`;
        statusArea.style.display = 'block';
        
        if (type === 'processing') {
            progressBar.style.display = 'block';
            progressFill.style.width = '0%';
        } else {
            progressBar.style.display = 'none';
        }
    }

    function hideStatus() {
        statusArea.style.display = 'none';
        progressBar.style.display = 'none';
    }
    
    function parseTimestampString(timestampStr) {
        // Parse "HH:MM:SS,mmm" format to seconds
        if (!timestampStr || typeof timestampStr !== 'string') {
            return null;
        }
        
        const match = timestampStr.match(/^(\d{2}):(\d{2}):(\d{2}),(\d{3})$/);
        if (!match) {
            return null;
        }
        
        const [, hours, minutes, seconds, milliseconds] = match;
        return parseInt(hours) * 3600 + parseInt(minutes) * 60 + parseInt(seconds) + parseInt(milliseconds) / 1000;
    }
    
    function formatTimestamp(seconds) {
        // Handle invalid or missing values
        if (typeof seconds !== 'number' || isNaN(seconds) || seconds < 0) {
            return '--:--';
        }
        
        const hours = Math.floor(seconds / 3600);
        const minutes = Math.floor((seconds % 3600) / 60);
        const secs = Math.floor(seconds % 60);
        
        if (hours > 0) {
            return `${hours}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
        } else {
            return `${minutes}:${secs.toString().padStart(2, '0')}`;
        }
    }
    
    function displayResults(data) {
        // Display summary
        summaryContent.textContent = data.summary;
        
        // Debug: log the transcript data structure
        console.log('Transcript data:', data.transcript);
        
        // Find transcript segments from different possible structures
        let segments = data.transcript.transcription || data.transcript.segments || data.transcript.results || [];
        
        // Display transcript with timestamps
        const transcriptHtml = segments.map(segment => {
            // Handle different possible timestamp formats
            let startTime, endTime;
            
            // Debug: log each segment
            console.log('Processing segment:', segment);
            
            if (segment.timestamps && segment.timestamps.from && segment.timestamps.to) {
                // whisper.cpp JSON format with string timestamps
                const startSeconds = parseTimestampString(segment.timestamps.from);
                const endSeconds = parseTimestampString(segment.timestamps.to);
                startTime = startSeconds ? formatTimestamp(startSeconds) : '--:--';
                endTime = endSeconds ? formatTimestamp(endSeconds) : '--:--';
            } else if (typeof segment.t0 === 'number' && typeof segment.t1 === 'number') {
                // Convert from centiseconds to seconds
                startTime = formatTimestamp(segment.t0 / 100);
                endTime = formatTimestamp(segment.t1 / 100);
            } else if (typeof segment.start === 'number' && typeof segment.end === 'number') {
                // Alternative format (seconds)
                startTime = formatTimestamp(segment.start);
                endTime = formatTimestamp(segment.end);
            } else if (segment.timestamp) {
                // Single timestamp format
                startTime = formatTimestamp(segment.timestamp);
                endTime = startTime;
            } else {
                // Fallback if no timestamps
                startTime = '--:--';
                endTime = '--:--';
            }
            
            return `<div class="transcript-segment">
                        <span class="timestamp">[${startTime} - ${endTime}]</span>
                        <span class="text">${segment.text || ''}</span>
                    </div>`;
        }).join('');
        
        transcriptContent.innerHTML = transcriptHtml;
        resultsArea.style.display = 'block';
    }

    function uploadFile(file) {
        if (!isValidFile(file)) {
            showStatus('Error: Only video and audio files are supported.', 'error');
            return;
        }

        const formData = new FormData();
        formData.append('file', file);
        formData.append('speaker_name', speakerName.value || 'Unknown Speaker');

        showStatus(`Processing ${file.name}... This may take a few minutes.`, 'processing');
        
        // Hide results from previous uploads
        resultsArea.style.display = 'none';
        
        // Simulate progress (since we can't get real progress from the server)
        let progress = 0;
        const progressInterval = setInterval(() => {
            progress += Math.random() * 10;
            if (progress > 90) progress = 90;
            progressFill.style.width = `${progress}%`;
        }, 1000);

        fetch('/upload', {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            clearInterval(progressInterval);
            progressFill.style.width = '100%';
            
            if (data.success) {
                showStatus('Processing completed successfully!', 'success');
                displayResults(data);
            } else {
                showStatus(data.error || 'Processing failed', 'error');
            }
        })
        .catch(error => {
            clearInterval(progressInterval);
            console.error('Error:', error);
            showStatus('Processing failed: Network error', 'error');
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