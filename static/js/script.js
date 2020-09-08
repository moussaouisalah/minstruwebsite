$(document).ready(function() {

    window.setInterval(function(){

        let downloadingP = $('.downloading');
        for(let i=0; i<downloadingP.length; i++) {
            let id = $(downloadingP[i]).parent().attr('id').replace('song', '');
            $.ajax({
            url : '/info/' + id,
            type : 'GET'
            }).then( (req) => {
                if(req.status == "ready"){
                    $(downloadingP[i]).parent().html(req.html);
                }
            } );
        }

    }, 5000);


});