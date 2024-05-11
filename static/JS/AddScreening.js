var Screenings;
var index = 0;

$(document).ready(function() {
    Screenings = document.getElementById("screenings");
    SetMinDate();

});

function AddScreening() {
    chosenStudio = document.getElementById('screening_studio').value;
    chosenDate = document.getElementById('screening_date').value;
    chosenTime = document.getElementById('screening_time').value;
    chosenCapacity = document.getElementById('screening_capacity').value;
    chosenPrice = document.getElementById('screening_price').value;

    if(!chosenStudio || !chosenDate || !chosenTime || !chosenCapacity || !chosenPrice)
        return;


    var newBaseDivDiv = document.createElement("div");
    newBaseDivDiv.className = "row justify-content-center";

    //studio
    var newStudioDiv = document.createElement("div");
    newStudioDiv.className = "col-12 col-md-2";

    var studioInnerDiv = document.createElement("div");
    studioInnerDiv.className = "row justify-content-center";

    var studioInputDiv = document.createElement("div");
    studioInputDiv.className = "col-6 col-md-12";

    var studioInputElement = document.createElement("input");
    studioInputElement.type = "text";
    studioInputElement.className = "form-control movie_info";
    studioInputElement.id = "screening_studio_" + index;
    studioInputElement.name = "screening_studio_" + index;
    studioInputElement.readOnly = true;
    studioInputElement.value = chosenStudio;

    studioInputDiv.appendChild(studioInputElement);
    studioInnerDiv.appendChild(studioInputDiv);
    newStudioDiv.appendChild(studioInnerDiv);

    //date
    var newDateDiv = document.createElement("div");
    newDateDiv.className = "col-12 col-md-2";

    var dateInnerDiv = document.createElement("div");
    dateInnerDiv.className = "row justify-content-center";

    var dateInputDiv = document.createElement("div");
    dateInputDiv.className = "col-6 col-md-12";

    var dateInputElement = document.createElement("input");
    dateInputElement.type = "text";
    dateInputElement.className = "form-control movie_info";
    dateInputElement.id = "screening_date_" + index;
    dateInputElement.name = "screening_date_" + index;
    dateInputElement.readOnly = true;
    dateInputElement.value = chosenDate;

    dateInputDiv.appendChild(dateInputElement);
    dateInnerDiv.appendChild(dateInputDiv);
    newDateDiv.appendChild(dateInnerDiv);

    //timeslot
    var newTimeslotDiv = document.createElement("div");
    newTimeslotDiv.className = "col-12 col-md-2";

    var timeSlotInnerDiv = document.createElement("div");
    timeSlotInnerDiv.className = "row justify-content-center";

    var timeslotInputDiv = document.createElement("div");
    timeslotInputDiv.className = "col-6 col-md-12";

    var timeSlotInputElement = document.createElement("input");
    timeSlotInputElement.type = "text";
    timeSlotInputElement.className = "form-control movie_info";
    timeSlotInputElement.id = "screening_time_" + index;
    timeSlotInputElement.name = "screening_time_" + index;
    timeSlotInputElement.readOnly = true;
    timeSlotInputElement.value = chosenTime;

    timeslotInputDiv.appendChild(timeSlotInputElement);
    timeSlotInnerDiv.appendChild(timeslotInputDiv);
    newTimeslotDiv.appendChild(timeSlotInnerDiv);


    //capacity
    var newCapacityDiv = document.createElement("div");
    newCapacityDiv.className = "col-12 col-md-2";

    var capacityInnerDiv = document.createElement("div");
    capacityInnerDiv.className = "row justify-content-center";

    var capacityInputDiv = document.createElement("div");
    capacityInputDiv.className = "col-6 col-md-12";

    var capacityInputElement = document.createElement("input");
    capacityInputElement.className = "form-control movie_info";
    capacityInputElement.id = "screening_capacity_" + index;
    capacityInputElement.name = "screening_capacity_" + index;
    capacityInputElement.readOnly = true;
    capacityInputElement.value = chosenCapacity;

    capacityInputDiv.appendChild(capacityInputElement);
    capacityInnerDiv.appendChild(capacityInputDiv);
    newCapacityDiv.appendChild(capacityInnerDiv);


     //price
    var newPriceDiv = document.createElement("div");
    newPriceDiv.className = "col-12 col-md-2";

    var priceInnerDiv = document.createElement("div");
    priceInnerDiv.className = "row justify-content-center";

    var priceInputDiv = document.createElement("div");
    priceInputDiv.className = "col-6 col-md-12";

    var priceInputElement = document.createElement("input");
    priceInputElement.className = "form-control movie_info";
    priceInputElement.id = "screening_price_" + index;
    priceInputElement.name = "screening_price_" + index;
    priceInputElement.readOnly = true;
    priceInputElement.value = chosenPrice;

    priceInputDiv.appendChild(priceInputElement);
    priceInnerDiv.appendChild(priceInputDiv);
    newPriceDiv.appendChild(priceInnerDiv);

     //delete button
    var newDeleteButtonDiv = document.createElement("div");
    newDeleteButtonDiv.className = "col-12 col-md-2";

    var deleteButtonInnerDiv = document.createElement("div");
    deleteButtonInnerDiv.className = "row justify-content-center";

    var deleteButtonInputDiv = document.createElement("div");
    deleteButtonInputDiv.className = "col-6 col-md-12";

    var deleteButtonElement = document.createElement("button");
    deleteButtonElement.id = "delete_button_" + index;
    deleteButtonElement.name = "delete_button_" + index;
    deleteButtonElement.className = "btn btn-secondary btn-md btn-block";
    deleteButtonElement.value = index;
    deleteButtonElement.textContent = "Delete"

    var breakLine = document.createElement("br");

    deleteButtonInputDiv.appendChild(deleteButtonElement);
    deleteButtonInnerDiv.appendChild(deleteButtonInputDiv);
    newDeleteButtonDiv.appendChild(deleteButtonInnerDiv);


    newBaseDivDiv.appendChild(newStudioDiv);
    newBaseDivDiv.appendChild(newDateDiv);
    newBaseDivDiv.appendChild(newTimeslotDiv);
    newBaseDivDiv.appendChild(newCapacityDiv);
    newBaseDivDiv.appendChild(newPriceDiv);
    newBaseDivDiv.appendChild(newDeleteButtonDiv);
    Screenings.appendChild(newBaseDivDiv);
    Screenings.appendChild(breakLine);
    index++;

    var numRows = document.getElementById("numRows");
    numRows.value = index;

    deleteButtonElement.onclick = function() {
    Screenings.removeChild(newBaseDivDiv);
    Screenings.removeChild(breakLine);

    //rename numbers
    for (i = 0; i < index; i++)
    {
        if(i <= this.value)
        {
            continue;
        }
        var studioToChange = document.getElementById("screening_studio_" + i);
        studioToChange.name = "screening_studio_" + (i - 1);
        studioToChange.id = "screening_studio_" + (i - 1);

        var dateToChange = document.getElementById("screening_date_" + i);
        dateToChange.name = "screening_date_" + (i - 1);
        dateToChange.id = "screening_date_" + (i - 1);

        var timeToChange = document.getElementById("screening_time_" + i);
        timeToChange.name = "screening_time_" + (i - 1);
        timeToChange.id = "screening_time_" + (i - 1);

        var capacityToChange = document.getElementById("screening_capacity_" + i);
        capacityToChange.name = "screening_capacity_" + (i - 1);
        capacityToChange.id = "screening_capacity_" + (i - 1);

        var priceToChange = document.getElementById("screening_price_" + i);
        priceToChange.name = "screening_price_" + (i - 1);
        priceToChange.id = "screening_price_" + (i - 1);

        var deleteButtonToChange = document.getElementById("delete_button_" + i);
        deleteButtonToChange.name = "delete_button_" + (i - 1);
        deleteButtonToChange.id = "delete_button_" + (i - 1);
        deleteButtonToChange.value = i - 1;
    }

    index--;
    numRows.value = index;
    }
}

function SetMinDate()
{
var today = new Date();
var tomorrow = new Date();
tomorrow.setDate(today.getDate() + 1);

var tomorrowFormatted = tomorrow.toISOString().split('T')[0];

var release_date = document.getElementById('movie_release_date');
var releaseDateValue = new Date(release_date.value);

if (release_date.value == '')
{
    release_date.setAttribute('min', tomorrowFormatted);
}

else if(releaseDateValue < today)
{
    release_date.readOnly = true;
}

document.getElementById('screening_date').setAttribute('min', tomorrowFormatted);
}