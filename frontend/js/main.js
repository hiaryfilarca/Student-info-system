document.addEventListener("DOMContentLoaded", function() {
    const readerElement = document.getElementById("reader");
    if (readerElement) {
        function onScanSuccess(decodedText, decodedResult) {
            try { html5QrcodeScanner.pause(); } catch (e) {}
            
            fetch('/api/attend', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ student_id: decodedText })
            })
            .then(response => response.json())
            .then(data => {
                const resultDiv = document.getElementById('result-message');
                resultDiv.style.display = 'block';
                if(data.success) {
                    resultDiv.className = 'alert alert-success';
                    resultDiv.innerText = data.message;
                } else {
                    resultDiv.className = 'alert alert-error';
                    resultDiv.innerText = data.message;
                    alert(data.message);
                }
                setTimeout(() => {
                    if (data.success || data.already_checked) {
                        window.location.href = '/';
                    } else {
                        resultDiv.style.display = 'none';
                        try { html5QrcodeScanner.resume(); } catch (e) {}
                    }
                }, 1500);
            })
            .catch(error => {
                console.error('Error:', error);
                try { html5QrcodeScanner.resume(); } catch(e) {}
            });
        }

        function onScanFailure(error) {}

        let html5QrcodeScanner = new Html5QrcodeScanner(
            "reader",
            { fps: 10, qrbox: { width: 250, height: 250 }, formatsToSupport: [ Html5QrcodeSupportedFormats.QR_CODE ],
                experimentalFeatures: { useBarCodeDetectorIfSupported: true } },
            false);
        html5QrcodeScanner.render(onScanSuccess, onScanFailure);
    }
});