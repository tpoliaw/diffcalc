'''
Created on 6 May 2016

@author: walton
'''
from diffcalc import settings
from diffcalc.gdasupport.scannable.sim import sim
import textwrap
from diffcalc.util import color


class ExternalCommand(object):
    """Instances found in a command_list by format_command_help will
    result in documentation for a command without there actually being one.
    """
    def __init__(self, docstring):
        """Set the docstring that will be pulled off by format_command_help.
        """
        self.__doc__ = docstring
        self.__name__ = ''


WIDTH = 27
INDENT = 3

def format_command_help(command_list):
    lines = []
    for obj in command_list:

        if isinstance(obj, basestring):  # group heading
            lines.extend(['', color.BOLD + obj.upper() + color.END, ''])

        else:  # individual command
            doc_before_empty_line = obj.__doc__.split('\n\n')[0]
            doc_lines = [s.strip() for s in doc_before_empty_line.split('\n')]
            for doc_line in doc_lines:
                if doc_line == '':
                    continue
                if obj.__name__ in ('ub', 'hkl'):
                    continue
                name, args, desc = _split_doc_line(doc_line)
                desc = desc.strip()
                if desc[-1] == '.':
                    desc = desc[:-1]
                
                cmd_lines = textwrap.wrap(name + ' ' + args, WIDTH,
                                          subsequent_indent='    ')
                desc_lines = textwrap.wrap(desc, 79 - INDENT - 3 - WIDTH)
                if not desc_lines:
                    raise AssertionError()
                
                first_line = True
                while cmd_lines or desc_lines:
                    line = ' ' * INDENT
                    if cmd_lines:
                        line += cmd_lines.pop(0).ljust(WIDTH)
                    else:
                        line += ' ' * (WIDTH)
                    line += ' : ' if first_line else '   '
                    if desc_lines:
                        line += desc_lines.pop(0)
                    lines.append(line)
                    first_line = False

    return '\n'.join(lines)


def _split_doc_line(docLine):
    name, _, right = docLine.partition(' ')
    args, _, desc = right.partition('-- ')
    return name, args, desc


def compile_extra_motion_commands_for_help():
    
    _hwname = settings.hardware.name
    _angles = ', '.join(settings.hardware.get_axes_names())
    
    commands = []
        
    commands.append('Motion')
    commands.append(sim)
    commands.append(ExternalCommand(
        '%(_hwname)s -- show Eularian position' % vars()))
    commands.append(ExternalCommand(
        'pos %(_hwname)s [%(_angles)s]  -- move to Eularian position'
        '(None holds an axis still)' % vars()))
    commands.append(ExternalCommand(
        'sim %(_hwname)s [%(_angles)s] -- simulate move to Eulerian position'
        '%(_hwname)s' % vars()))
    
    commands.append(ExternalCommand(
        'hkl -- show hkl position'))
    commands.append(ExternalCommand(
        'pos hkl [h k l] -- move to hkl position'))
    commands.append(ExternalCommand(
        'pos {h | k | l} val -- move h, k or l to val'))
    commands.append(ExternalCommand(
        'sim hkl [h k l] -- simulate move to hkl position'))
    
#     if engine_name != 'vlieg':
#         pass
#         # TODO: remove sigtau command and 'Surface' string
    return commands