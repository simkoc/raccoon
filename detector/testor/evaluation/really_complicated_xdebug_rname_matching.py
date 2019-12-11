"""
WHEN GENERATING THE POSSIBLE URLS I NEED TO KNOW WHAT PARAMETERS
ARE CONSTANTS AND WHAT ARE NOT FOR COMPARISION e.g.
route=a/b/c
"""
import warnings


class Url():

    def __init__(self, url):
        if len(url.split("?")) == 2:
            message_uri = url.split("?")[0]
            message_query = url.split("?")[1]
        else:
            message_uri = url.split("?")[0]
            message_query = ""

        message_uri_split = message_uri.split("/")
        print message_uri_split
        self._schema = message_uri_split[0]
        self._domain = message_uri_split[2]
        self._uri = "/{}".format("/".join(message_uri_split[3:]))

        self._query_elements = []
        if message_query != "":
            for elem in message_query.split("&"):
                self._query_elements.append([elem.split("=")[0],
                                             elem.split("=")[1]])

    def annote_variable_type(self, connotation_dictionary):
        new = []
        for param_pair in self._query_elements:
            if param_pair[0] in connotation_dictionary:
                new.append([param_pair[0], param_pair[1], connotation_dictionary[param_pair[0]]])
            else:
                warnings.warn("parameter {} has unknown variable type".format(param_pair[0]))
        self._query_elements = new

    def __str__(self):
        ret = "{}//{}{}".format(self._schema, self._domain, self._uri)
        if self._query_elements != []:
            ret = "{}?".format(ret)
        for elem in self._query_elements:
            ret = "{}&{}={}".format(ret, elem[0], elem[1])
        return ret

    def __repr__(self):
        return self.__str__()


def generate_all_possible_query_strings(query_components):
    """
    generates all possible query strings based on the query
    components contained in the %R xdebug name value (after php)
    based on the question/answer at
    https://stackoverflow.com/questions/47790131/replacement-rules-of-xdebug-name-parameter-r/47793866#47793866
    """
    ret = []

    if query_components == []:
        return ret

    for ret in generate_all_possible_query_strings(query_components[1:]):
        ret.append("{}/{}".format(query_components[0], ret))
        ret.append("{}\{}".format(query_components[0], ret))
        ret.append("{}.{}".format(query_components[0], ret))
        ret.append("{}?{}".format(query_components[0], ret))
        ret.append("{}&{}".format(query_components[0], ret))
        ret.append("{}+{}".format(query_components[0], ret))
        ret.append("{}:{}".format(query_components[0], ret))
        ret.append("{}*{}".format(query_components[0], ret))
        ret.append("{}|{}".format(query_components[0], ret))

    return ret


def get_all_possible_parameter_candidate_lists(query_strings):
    """
    iterates over all query strings and splits them into a
    list of parameters containing the name and the value
    as a pair
    """
    ret = []
    for string in query_strings:
        split = string.split("&")
        buff = []
        for elem in split:
            buff.append([elem.split("=")[0], elem.split("=")[1]])
        ret.append(buff)
    return ret


"""
How to counteract underrepresentatiion?
"""
def get_best_query_candidate(xdebug_uri_query, parameter_candidates):
    """
    matches all possible query parameter candidates against the candidates
    given as a parameter. The best matching candidate list wins and
    is returned. However, a optimal match ratio smaller 1 results
    in a warning as we do not expect on encountering any new parameters
    """
    candidate_lists = get_all_possible_parameter_candidate_lists(
        generate_all_possible_query_strings(xdebug_uri_query))
    best = []
    fittage = -1
    for candidate_list in candidate_lists:
        fit_counter = 0
        for candidate_pair in candidate_list:
            if parameter_candidates.find(candidate_pair[0]) != -1:
                fit_counter = fit_counter + 1
        fittage_buff = float(fit_counter)/float(len(candidate_list))
        if fittage_buff == 1:
            return candidate_list
        elif fittage_buff > fittage:
            fittage = fittage_buff
            best = candidate_list

    if fittage != 1:
        warnings.warn("best fitting query list {} has only fitting ratio of {}".format(best, fittage))

    ret_string = ""
    for pair in best:
        ret_string = "{}={}&".format(pair[0], pair[1])
    return ret_string[:-1]


def get_all_possible_uri_candidates(xdebug_uri_path):
    """
    generates all possible uris based on the xdebug %R part
    up to (and including) php. It uses the assumtion that
    in the uri only _ and / are used
    """
    reta = []

    if xdebug_uri_path == []:
        raise Exception("well we reached the end without php, that is weird")

    if xdebug_uri_path == ["php"]:
        return ["php"]

    for ret in get_all_possible_uri_candidates(xdebug_uri_path[1:]):
        #  reductive assumption '_' in the uri path is either _ or / or .
        reta.append("{}/{}".format(xdebug_uri_path[0], ret))
        reta.append("{}_{}".format(xdebug_uri_path[0], ret))
        reta.append("{}.{}".format(xdebug_uri_path[0], ret))

    return reta


def get_best_uri_candidate(xdebug_uri_path, path_candidates):
    """
    matches all generated paths against all possible paths
    given as a parameter. Raises an error in case no
    match was found
    """
    for uri in get_all_possible_uri_candidates(xdebug_uri_path):
        if uri in path_candidates:
            return uri

    raise Exception("no fitting candidate contained in {} for list {}".format(xdebug_uri_path, path_candidates))


def get_deep_model_url_candidates(graph, projname, session, user):
    """
    returns a list of Url objects that store all the Urls contained
    in the deep model of Deemon for the project. session, user
    """
    query = """MATCH (e:Event {dm_type:'HttpRequest', projname:'%s', session:'%s', user:'%s'}) RETURN e.message;""" % (projname,
                                                                                                                      session,
                                                                                                                      user)
    ret = []
    res = graph.data(query)
    for re in res:
        message = re["e.message"]
        if message[0:3] == "GET":
            message = message[4:]
        elif message[0:4] == "POST":
            message = message[5:]
        else:
            raise Exception("unknown message schema in message {}".format(message))

        ret.append(Url(message))

    return ret


def recreate_best_url_candidate(r_name,
                                graph, projname, session, user):
    """
    recreates the best fitting url of a xdebug %R name by generating all
    possible names and cross referencing them with the stored urls in
    the deep model of Deemon
    """
    split = r_name.split("_")
    index = split.index("php")
    urls = get_deep_model_url_candidates(graph,
                                         projname,
                                         session,
                                         user)
    query = get_best_query_candidate(split[index+2:],
                                     [url._query_elements for url in urls])
    uri = get_best_uri_candidate(split[:index+1],
                                 [url._uri for url in urls])
    if query == "":
        return uri
    else:
        return "{}?{}".format(uri, query)


def name_surjective_equal_p(namelhs, namerhs, logger=None):
    def split_empty(split):
        if len(split) == 2:
            if split[0] == '' and split[1] == '':
                return True
        return False

    if logger is not None:
        logger.debug("comparing {} vs. {}".format(namerhs, namelhs))

    lhsconstants = sorted(get_only_constant_url_parts(namelhs))
    rhsconstants = sorted(get_only_constant_url_parts(namerhs))

    print lhsconstants, rhsconstants

    if len(lhsconstants) != len(rhsconstants):
        if logger is not None:
            logger.debug("the constants of either name are not same length")
            logger.debug("{} vs. {}".format(lhsconstants, rhsconstants))
        return False
    else:
        for lhs, rhs in zip(lhsconstants, rhsconstants):
            if lhs != rhs:
                if logger is not None:
                    logger.debug(
                        "names differ at constant {} vs. {}".format(lhs, rhs))
                return False

    return True
