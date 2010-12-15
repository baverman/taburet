fun({Doc}) ->
	case proplists:get_value(<<"doc_type">>, Doc) of
		<<"Transaction">> ->
			Amount = proplists:get_value(<<"amount">>, Doc),
			[Year, Month, Day|_] = proplists:get_value(<<"date">>, Doc), 
			FromAccId = lists:last(proplists:get_value(<<"from_acc">>, Doc)),
			ToAccId = lists:last(proplists:get_value(<<"to_acc">>, Doc)),
			
			Emit([FromAccId, Year, Month, Day], {[{debet, 0.0}, {kredit, Amount}]}),
			Emit([ToAccId, Year, Month, Day], {[{debet, Amount}, {kredit, 0.0}]});
		_ -> ok
	end
end.
