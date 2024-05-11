function myFunction(clicked_button) {
    //  alert(clicked_button);
        switch (clicked_button) {
            case  "personal-information-edit-button":
            case  "personal-information-view-button":
                $("#personal-information-edit").toggleClass('d-none');
                $("#personal-information-view").toggleClass('d-none');
                break;
    
            case  "order-history-edit-button":
            case  "order-history-view-button":
                $("#order-history-edit").toggleClass('d-none');
                $("#order-history-view").toggleClass('d-none');
                break;
    
            case  "change-password-edit-button":
            case  "change-password-check-button":
                $("#change-password-edit").toggleClass('d-none');
                $("#change-password-check").toggleClass('d-none');
                break;
    
        }
}