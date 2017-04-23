function toggle_flag_button(){
    $('#toggle-flag').toggleClass('activated');
    $('#toggle-flag').toggleClass('not-activated');
    if ($('#toggle-flag').prop('value') == 'clear'){
        $('#toggle-flag').prop('value', 'flag');
    } else {
        $('#toggle-flag').prop('value', 'clear');
    }
}

function reset_game(url, game_id){
    $('#message').html('');
    $.ajax({
        url: url,
        data: {
            'game_id': game_id
        },
        dataType: 'json',
        success: function (data) {
            update_boardstate(
                data.game_status,
                data.message,
                data.json_boardstate
            );
        }
    });
}

function submit_move(url,game_id, x, y, move_type) {
    $.ajax({
        url: url,
        data: {
            'game_id': game_id,
            'x': x,
            'y': y,
            'move_type': move_type
        },
        dataType: 'json',
        success: function (data) {
            update_boardstate(
                data.game_status,
                data.message,
                data.json_boardstate
            );
        }
    });
}

function render_new_game_modal(url) {
    var csrftoken = getCookie('csrftoken');
    $('.new_game_modal_container').html('').load(
        url,
        {
            'csrfmiddlewaretoken': csrftoken,
        },
        function(){
            $('.dossier_summary_modal').modal('show');
        }
    );
}

function update_boardstate(game_status, message, boardstate) {
    console.log(game_status);
    var boardstate_obj = $.parseJSON(boardstate);
    $.each(boardstate_obj, function(index_x, row) {
        $.each(row, function(index_y, column) {
            var $btn = $("button[x$='" + index_x +"'][y$='" +index_y+ "']");
            if (column !== null){
                if (column == 'mined'){
                $btn.attr('class', 'location bomb').html('<i class="fa fa-bomb" aria-hidden="true"></i>');
                } else if(column == 'flagged') {
                    $btn.attr('class', 'location flag').html('<i class="fa fa-flag" aria-hidden="true"></i>');
                } else {
                    $btn.attr('class', 'location visible');
                    if (column === 0) {
                        $btn.html('');
                    } else {
                        $btn.html(column);
                    }
                }
            } else{
                $btn.html('').attr('class', 'location');
            }
        });
    });
    if (game_status !== 0){
        var modal_title = '';
        if (game_status==1) {
            modal_title = 'You Win!';
        } else {
            modal_title = 'You Lose!';
        }
        $('#message').html(message);
        $('#modal_title').html(modal_title);
        $('#newgamesubmit').html('Play Again');
        $('#newgamemodal').modal('show');

    }
}
