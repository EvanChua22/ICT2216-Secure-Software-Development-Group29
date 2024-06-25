document.getElementById('image').addEventListener('change', function(event) {
    var reader = new FileReader();
    reader.onload = function(){
        var output = document.getElementById('image-preview');
        output.src = reader.result;
        output.style.display = 'block';

        output.style.maxWidth = '200px'; // Set maximum width
        output.style.maxHeight = '200px'; // Set maximum height
        };
    reader.readAsDataURL(event.target.files[0]);
});
