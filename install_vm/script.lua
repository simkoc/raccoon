local DEBUG = "False"

local hoi = "BOGUS"


function sanitize(query)
        query = string.gsub(query, "\n", " ")
        query = string.gsub(query, "\t", " ")
        return string.gsub(query, "`", " ")
end

function normalize(query)
	 cmd = "/home/bitnami/hashQuery.pex " .. "\"" .. query .. "\""
         local fh = assert(io.popen(cmd, 'r'))
         local data = fh:read('*all')
	 fh:close()	
         return data
end


function read_query(packet)
	ret = nil
	-- lines = get_lines_of_file("/opt/suspendSingleQuery.txt")
	-- comp_query = sanitize(lines[1])

	if string.byte(packet) == proxy.COM_QUERY then	
		query = sanitize(packet:sub(2))
                query_low = string.lower(query)		

                if string.sub(query_low,0,6) == "select" then
                   return nil
                end

		-- comp_hash = normalize(comp_query)
		comp_hash = hoi
		query_hash = normalize(query)

		print(query_hash .. "->" .. query)
                
		if comp_hash == query_hash then
		        print("match - inserting delay")
			inj_query = "SELECT sleep(60);"
			new_packet = string.char(proxy.COM_QUERY) .. inj_query
			proxy.queries:append(1, new_packet, { resultset_is_needed = true })
			proxy.queries:append(2, packet, { resultset_is_needed = true })
			ret = proxy.PROXY_SEND_QUERY
		end
	end
	return ret
end


function read_query_result(inj)
	if inj.id == 1 then
		if DEBUG then
			print("sleep query returns")
		end
		return proxy.PROXY_IGNORE_RESULT
	end
	if inj.id == 2 then
		if DEBUG then
			print("regular query returns")
		end
		return
	end
	return
end
