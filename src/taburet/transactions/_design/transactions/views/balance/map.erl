fun({Doc}) ->
	case proplists:get_value(<<"doc_type">>, Doc) of
		<<"Transaction">> ->
			Amount = proplists:get_value(<<"amount">>, Doc),
			
			lists:foreach(
				fun(AccId)-> Emit(AccId, {[{debet, 0.0}, {kredit, Amount}]}) end,
				proplists:get_value(<<"from_acc">>, Doc)
			),
			
			lists:foreach(
				fun(AccId)-> Emit(AccId, {[{debet, Amount}, {kredit, 0.0}]}) end,
				proplists:get_value(<<"to_acc">>, Doc)
			);
		_ -> ok
	end
end.
