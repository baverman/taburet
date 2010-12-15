fun({Doc}) ->
	case proplists:get_value(<<"doc_type">>, Doc) of
		<<"Transaction">> ->
			[Year, Month, Day | _] = proplists:get_value(<<"date">>, Doc),
			FromAccId = lists:last(proplists:get_value(<<"from_acc">>, Doc)),
			ToAccId = lists:last(proplists:get_value(<<"to_acc">>, Doc)),
			Emit([2, FromAccId, Year, Month, Day], null),
			Emit([1, ToAccId, Year, Month, Day], null),
			Emit([3, FromAccId, Year, Month, Day], null),
			Emit([3, ToAccId, Year, Month, Day], null);
		_ -> ok
	end
end.
