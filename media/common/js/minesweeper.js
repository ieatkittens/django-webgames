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
                data['game_status'],
                data['message'],
                data['json_boardstate']
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
                data['game_status'],
                data['message'],
                data['json_boardstate']
            );
        }
    });
}

function update_boardstate(game_status, message, boardstate) {
    var boardstate_obj = $.parseJSON(boardstate);
    $('#message').html(message);
    $.each(boardstate_obj, function(index_x, row) {
        $.each(row, function(index_y, column) {
            var $btn = $("button[x$='" + index_x +"'][y$='" +index_y+ "']");
            if (column != 'not_visible'){
                if (column == -1){
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
}
