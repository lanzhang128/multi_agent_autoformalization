def isabelle_get_error_details(finished_response):
    error_details = []
    error_lines = []

    if finished_response is not None:
        assert finished_response[0] == 'FINISHED'
        response_body = finished_response[1]
        if response_body['ok']:
            is_valid = True
            if len(response_body['errors']) != 0:
                print('Isabelle server command \"use_theories\" did not act as expected.')
                is_valid = False
        else:
            is_valid = False

        for error in response_body['errors']:
            message = error['message']
            pos = error['pos']
            line, offset, end_offset = pos['line'], pos['offset'], pos['end_offset']
            error_details.append(f'Error on line {line}, start {offset}, end {end_offset}: {message}')
            error_lines.append(line)

    else:
        print('Not Finished.')
        is_valid = False
    return is_valid, error_lines, error_details
