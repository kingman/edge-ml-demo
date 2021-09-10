
$(document).ready(function() {

	$('form').on('submit', function(event) {

		$.ajax({
			data : {
				threshold : $('#threshold').val()
			},
			type : 'POST',
			url : '/store_data'
		})
		.done(function(data) {

			if (data.enabled) {
                $('#storeInfo').text(`Data capture is enabled, with threshold value ${data.threshold}`).show();
                $('button').html('Disable Storage');
			} else {
                $('#storeInfo').hide();
                $('button').html('Enable Storage');
			}

		});

		event.preventDefault();

	});

});