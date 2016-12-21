import subprocess
import re


def run_verifyta(xml, queries, *args, verifyta):
    """
    :param xml: string giving the path to a uppaal project XML file
    :param queries: string giving the path to a uppaal query file
    :param *args: other args giving to verifyta, e.g. -t 2 for getting the fastest trace.
    :param verifyta: string giving the path to verifyta
    :return 0: Returns the standard output, i.e. if the queries were satisfied
    :return 1: Returns the trace(s) of the queries.
    """
    res = subprocess.run([verifyta, xml, queries] + list(args), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return res.stdout, res.stderr   # ResultBin, Trace

def trace_time(trace, clock_name='global_c'):
    """
    :param trace: The trace represented as bytes given by uppaal, from which we find the last value of a global clock.
    :param clock_name: A string representing the name of the global clock from which we will extract a value
    :return: An integer representing the last clock value
    """
    trace_str = trace.decode('utf-8')
    lst = trace_str.splitlines()
    try:
        s = str(lst[-1])    # The information we want is on the last line
        res = re.search(clock_name + ".?(=)(\d+)", s).group(2)
    except (IndexError, AttributeError):
        raise RuntimeError('Could not acquire the time from the trace\n Trace:\n' + trace_str)
    return int(res)


def property_satisfied(result):
    """
    :param result: binary string with a result from UPPAAL CORA
    :return: Boolean, False if some query did not succeed, True if all queries succeeded
    """
    s = result.decode("utf-8")
    if re.search('-- Formula is NOT satisfied.', s) or len(s) < 1:
        return False
    else:
        return True


def pprint(bytestring):
    print(bytestring.decode('utf-8'))



