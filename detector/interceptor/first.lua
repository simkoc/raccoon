-- first.lua
function get_lines_of_file(file)
	lines = {}
	for line in io.lines(file) do
		lines[#lines + 1] = line
	end
	return lines
end

function read_query(packet)
	if string.byte(packet) == proxy.COM_QUERY then	
		print(">>>>>>>>>>>>>")
		print ("got query " .. string.sub(packet, 2))
		lines = get_lines_of_file("suspendSingleQuery.txt")
		print ("read stuff")
		query = lines[1]	
		if query ~= nil then
			print("compare with " .. query)
			if query == string.sub(packet, 2) then
				print("match")
			else
				print("no match")
			end
		end
	end
end
