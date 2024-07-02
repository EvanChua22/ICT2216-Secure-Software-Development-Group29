document.addEventListener('DOMContentLoaded', function() {
            document.getElementById('image').addEventListener('change', function(event) {
                const file = event.target.files[0];
                if (file) {
                    // Check if the file type starts with 'image/'
                    if (!file.type.startsWith('image/')) {
                        alert('Please upload a valid image file.');
                        event.target.value = ''; // Clear the file input
                        document.getElementById('image-preview').style.display = 'none';
                        return;
                    }

                    // Read the file as a Data URL and check its contents
                    var reader = new FileReader();
                    reader.onload = function() {
                        // Create an Image object
                        var img = new Image();
                        img.onload = function() {
                            // File is a valid image, display it
                            var output = document.getElementById('image-preview');
                            output.src = reader.result;
                            output.style.display = 'block';
                            output.style.maxWidth = '200px'; // Set maximum width
                            output.style.maxHeight = '200px'; // Set maximum height
                        };
                        img.onerror = function() {
                            // File is not a valid image
                            alert('Please upload a valid image file.');
                            event.target.value = ''; // Clear the file input
                            document.getElementById('image-preview').style.display = 'none';
                        };
                        img.src = reader.result;
                    };
                    reader.readAsDataURL(file);
                }
            });
        });

/*document.getElementById('image').addEventListener('change', function(event) {
    var reader = new FileReader();
    reader.onload = function(){
        var output = document.getElementById('image-preview');
        output.src = reader.result;
        output.style.display = 'block';

        output.style.maxWidth = '200px'; // Set maximum width
        output.style.maxHeight = '200px'; // Set maximum height
        };
    reader.readAsDataURL(event.target.files[0]);
});*/
