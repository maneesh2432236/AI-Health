document.addEventListener('DOMContentLoaded', function () {
    const themeButtons = document.querySelectorAll('.theme-toggle');
    const savedTheme = localStorage.getItem('aiHealthTheme') || 'light';
    document.body.classList.toggle('theme-light', savedTheme === 'light');
    document.body.classList.toggle('theme-dark', savedTheme === 'dark');
    applyThemeIcon(savedTheme);

    themeButtons.forEach((button) => {
        button.addEventListener('click', () => {
            const current = document.body.classList.contains('theme-light') ? 'light' : 'dark';
            const next = current === 'light' ? 'dark' : 'light';
            document.body.classList.toggle('theme-light', next === 'light');
            document.body.classList.toggle('theme-dark', next === 'dark');
            localStorage.setItem('aiHealthTheme', next);
            applyThemeIcon(next);
        });
    });

    function applyThemeIcon(theme) {
        const icons = document.querySelectorAll('.theme-toggle i');
        icons.forEach((icon) => {
            icon.className = theme === 'light' ? 'bi bi-moon-stars' : 'bi bi-sun';
        });
    }

    const setupUpload = (uploadInputId, uploadAreaId, previewImageId, previewPlaceholderSelector) => {
        const uploadInput = document.getElementById(uploadInputId);
        const uploadArea = document.getElementById(uploadAreaId);
        const previewImage = document.getElementById(previewImageId);
        const previewPlaceholder = uploadArea?.querySelector(previewPlaceholderSelector || '.upload-placeholder');

        if (!uploadInput || !uploadArea || !previewImage) return;

        uploadArea.addEventListener('click', () => uploadInput.click());

        const onFileSelected = (file) => {
            if (!file) return;
            const reader = new FileReader();
            reader.onload = (event) => {
                previewImage.src = event.target.result;
                previewImage.hidden = false;
                if (previewPlaceholder) previewPlaceholder.style.display = 'none';
            };
            reader.readAsDataURL(file);
        };

        uploadInput.addEventListener('change', (event) => onFileSelected(event.target.files[0]));

        ['dragenter', 'dragover'].forEach((eventName) => {
            uploadArea.addEventListener(eventName, (event) => {
                event.preventDefault();
                uploadArea.classList.add('dragover');
            });
        });

        ['dragleave', 'drop'].forEach((eventName) => {
            uploadArea.addEventListener(eventName, (event) => {
                event.preventDefault();
                uploadArea.classList.remove('dragover');
            });
        });

        uploadArea.addEventListener('drop', (event) => {
            const file = event.dataTransfer.files[0];
            if (file) {
                uploadInput.files = event.dataTransfer.files;
                onFileSelected(file);
            }
        });
    };

    setupUpload('imageUpload', 'uploadArea', 'previewImage', '.upload-placeholder');
    setupUpload('imageUploadSkin', 'uploadAreaSkin', 'previewImageSkin', '.upload-placeholder');

    const attachCameraHandlers = (cameraBtnId, captureBtnId, retakeBtnId, videoId, canvasId, dataUrlId, previewImageId) => {
        const startButton = document.getElementById(cameraBtnId);
        const captureButton = document.getElementById(captureBtnId);
        const retakeButton = document.getElementById(retakeBtnId);
        const video = document.getElementById(videoId);
        const canvas = document.getElementById(canvasId);
        const dataUrlNode = document.getElementById(dataUrlId);
        const previewImage = document.getElementById(previewImageId);
        const previewPlaceholder = video?.parentElement?.querySelector('.preview-placeholder') || document.querySelector('.preview-placeholder');

        if (!startButton || !video || !canvas || !dataUrlNode || !previewImage) return;

        let stream = null;

        startButton.addEventListener('click', async () => {
            try {
                stream = await navigator.mediaDevices.getUserMedia({ video: true, audio: false });
                video.srcObject = stream;
                video.classList.add('active');
                video.play();
                captureButton.disabled = false;
                retakeButton.hidden = false;
            } catch (error) {
                alert('Camera access was denied or unavailable. Please upload an image instead.');
            }
        });

        captureButton.addEventListener('click', () => {
            if (!stream) {
                alert('Please start the camera before capturing an image.');
                return;
            }
            const context = canvas.getContext('2d');
            canvas.width = video.videoWidth || 640;
            canvas.height = video.videoHeight || 480;
            context.drawImage(video, 0, 0, canvas.width, canvas.height);
            const dataUrl = canvas.toDataURL('image/jpeg', 0.92);
            dataUrlNode.value = dataUrl;
            previewImage.src = dataUrl;
            previewImage.hidden = false;
            if (previewPlaceholder) previewPlaceholder.style.display = 'none';
            if (stream) {
                stream.getTracks().forEach((track) => track.stop());
                video.srcObject = null;
            }
        });

        retakeButton.addEventListener('click', async () => {
            dataUrlNode.value = '';
            previewImage.hidden = true;
            if (stream) {
                stream.getTracks().forEach((track) => track.stop());
            }
            try {
                stream = await navigator.mediaDevices.getUserMedia({ video: true, audio: false });
                video.srcObject = stream;
                video.classList.add('active');
                video.play();
            } catch (error) {
                alert('The camera could not be reopened. Please upload a file instead.');
            }
        });
    };

    attachCameraHandlers('startCameraBtn', 'captureBtn', 'retakeBtn', 'cameraStream', 'cameraCanvas', 'cameraDataUrl', 'previewImage');
    attachCameraHandlers('startCameraBtnSkin', 'captureBtnSkin', 'retakeBtnSkin', 'cameraStreamSkin', 'cameraCanvasSkin', 'cameraDataUrlSkin', 'previewImageSkin');
});
