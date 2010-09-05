fun(Keys, Values, ReReduce) ->
	{Debet, Kredit, Before} = lists:foldl(
		fun(V, {OD,OK,OB}) ->
			{[{<<"debet">>, D}, {<<"kredit">>, K}, {<<"before">>, B}|_]} = V,
			{D + OD, K + OK, B + OB}
		end,
		{0, 0, 0},
		Values
	),

	{[
		{debet, erlang:round(Debet*100.0)/100.0},
		{kredit, erlang:round(Kredit*100.0)/100.0},
		{before, erlang:round(Before*100.0)/100.0},
		{'after', erlang:round((Before+Debet-Kredit)*100.0)/100.0}
	]}
end.
