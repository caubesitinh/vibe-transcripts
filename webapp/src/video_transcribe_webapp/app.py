from flask import Flask, render_template, request, jsonify
import os

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 4 * 1024 * 1024 * 1024  # 4GB max file size

# Allowed video file extensions
ALLOWED_EXTENSIONS = {
    'mp4', 'avi', 'mov', 'mkv', 'wmv', 'flv', 'webm', 'm4v', '3gp'
}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if not allowed_file(file.filename):
        return jsonify({'error': 'Invalid file type. Only video files are allowed.'}), 400
    
    # For now, we just throw away the file as requested
    # In the future, this is where transcription would happen
    
    return jsonify({
        'success': True, 
        'message': f'Video file "{file.filename}" uploaded successfully (discarded for now)'
    })

if __name__ == '__main__':
    app.run(debug=True)