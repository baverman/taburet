fun({Doc}) ->
	case proplists:get_value(<<"doc_type">>, Doc) of
		<<"Transaction">> ->
			Amount = proplists:get_value(<<"amount">>, Doc),
			[Year, Month | _] = proplists:get_value(<<"date">>, Doc), 
			FromAccs = proplists:get_value(<<"from_acc">>, Doc),
			ToAccs = proplists:get_value(<<"to_acc">>, Doc),
			
			if Year < %(year)d orelse (Year == %(year)d andalso Month < %(month)d) ->
				lists:foreach(fun(AccId)-> Emit(AccId, {[{debet, 0.0}, {kredit, 0.0}, {before, -Amount}]}) end, FromAccs),
				lists:foreach(fun(AccId)-> Emit(AccId, {[{debet, 0.0}, {kredit, 0.0}, {before, Amount}]}) end, ToAccs);
			Year == %(year)d andalso Month == %(month)d ->
				lists:foreach(fun(AccId)-> Emit(AccId, {[{debet, 0.0}, {kredit, Amount}, {before, 0.0}]}) end, FromAccs),
				lists:foreach(fun(AccId)-> Emit(AccId, {[{debet, Amount}, {kredit, 0.0}, {before, 0.0}]}) end, ToAccs);
			true ->
				ok
			end;
		_ -> ok
	end
end.
