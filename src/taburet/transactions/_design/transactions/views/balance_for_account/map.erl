fun({Doc}) ->
	case proplists:get_value(<<"doc_type">>, Doc) of
		<<"Transaction">> ->
			Amount = proplists:get_value(<<"amount">>, Doc),
			[Year, Month, Day|_] = proplists:get_value(<<"date">>, Doc), 
			
			lists:foreach(
				fun(AccId)-> Emit([AccId, Year, Month, Day], {[{debet, 0.0}, {kredit, Amount}]}) end,
				proplists:get_value(<<"from_acc">>, Doc)
			),
			
			lists:foreach(
				fun(AccId)-> Emit([AccId, Year, Month, Day], {[{debet, Amount}, {kredit, 0.0}]}) end,
				proplists:get_value(<<"to_acc">>, Doc)
			);
		_ -> ok
	end
end.
