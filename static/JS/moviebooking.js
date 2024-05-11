$(document).ready(function(){
    const $studioSelect = $("#studioSelect");
    const $dateSelect = $("#dateSelect");
    const $timeSelect = $("#timeSelect");
    const $capacityDisplay = $(".capacity-display");
    const $priceDisplay = $(".price-display")
    const $ticketCounter = $(".ticket-counter");
    const $btnIncrement = $(".btn-increment");
    const $btnDecrement = $(".btn-decrement");
    let screeningsData = {};

    function updateButtonState(capacity) {
        $btnIncrement.prop('disabled', capacity <= 0 || parseInt($ticketCounter.val()) >= capacity);
        $btnDecrement.prop('disabled', parseInt($ticketCounter.val()) <= 1);
    }

    function getCurrentCapacity() {
        const match = $capacityDisplay.text().match(/(\d+)\/\d+/);
        return match ? parseInt(match[1], 10) : 0;
    }

    $btnIncrement.add($btnDecrement).prop('disabled', true);

    $studioSelect.on("change", function() {
        const studioId = $(this).val();
        const filmId = window.filmId;

        $dateSelect.html('<option>Select Date</option>');
        $timeSelect.html('<option>Select Time</option>');
        $capacityDisplay.text("Capacity -/-");
        $priceDisplay.text("-")
        $ticketCounter.val("1");
        updateButtonState(0);

        if(studioId) {
            $.getJSON(`/get_screenings/${filmId}/${studioId}`, data => {
            screeningsData = data;
            const dateOptions = Object.keys(data).map(date => `<option value="${date}">${date}</option>`).join('');
            $dateSelect.append(dateOptions);
            });
        }
    });

    $dateSelect.on("change", function() {
        const selectedDate = $(this).val();
        $timeSelect.html('<option>Select Time</option>');
        updateButtonState(0);
        $priceDisplay.text("-");
        $capacityDisplay.text("Capacity -/-");
        if(selectedDate && screeningsData[selectedDate]) {
            const timeOptions = screeningsData[selectedDate].map(screening => `<option value="${screening.time}" data-capacity="${screening.capacity}" data-originalCapacity="${screening.originalCapacity}" data-id="${screening.screeningId}" data-price="${screening.screeningPrice}">${screening.time}</option>`).join('');
            $timeSelect.append(timeOptions);
        }
    });

    $timeSelect.on("change", function() {
        const totalCapacity = $("option:selected", this).attr("data-originalCapacity");
        const availableSeats = $("option:selected", this).attr("data-capacity");
        const selectedScreeningId = $("option:selected", this).data("id");
        const selectedPrice = $("option:selected", this).data("price");
        // Set the selectedScreeningId to the input field
        $('input[name="screeningId"]').val(selectedScreeningId);
        $priceDisplay.text(`${selectedPrice}`);
        $('#hiddenPrice').val(selectedPrice);

        if (totalCapacity && availableSeats) {
            $capacityDisplay.text(`Capacity ${availableSeats}/${totalCapacity}`);
            updateButtonState(availableSeats);
        } else {
            $capacityDisplay.text("Capacity -/-");
            $priceDisplay.text("-");
            updateButtonState(0);
        }
        updatePaymentButtonState();
    });

    $btnIncrement.click(() => {
        const currentCount = parseInt($ticketCounter.val());
        const currentCapacity = getCurrentCapacity();
        if (currentCount < currentCapacity) {
            $ticketCounter.val(currentCount + 1);
                updateButtonState(currentCapacity);
        }
    });

    $btnDecrement.click(() => {
        const currentCount = parseInt($ticketCounter.val());
        if (currentCount > 1) {
            $ticketCounter.val(currentCount - 1);
            updateButtonState(getCurrentCapacity());
            }
    });

    function allSelectionsMade() {
        // Check if all dropdowns have a selected value other than the default
        return $studioSelect.val() !== "Select Studio" && $dateSelect.val() !== "Select Date" && $timeSelect.val() !== "Select Time";
    }

    function updatePaymentButtonState() {
        const availableSeats = getCurrentCapacity();
        $('.proceed-to-payment-btn').prop('disabled', !allSelectionsMade() || availableSeats <= 0);
    }
        // Trigger the check whenever any dropdown value changes
        $studioSelect.on("change", updatePaymentButtonState);
        $dateSelect.on("change", updatePaymentButtonState);
        $timeSelect.on("change", updatePaymentButtonState);
    });
