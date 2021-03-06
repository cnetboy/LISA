#coding=utf-8
'''
    dst_ip = RangeItem(1000, 1000)
    
    sw_1 = DotItem(1)
    # src_ip1 = RangeItem(500, 2000)
    # dst_ip1 = RangeItem(1000, 1000)
    # vlan1 = SetItem([1, 2, 3])
    # port1 = DotItem(80)
    
    sw_2 = DotItem(2)
    # src_ip2 = RangeItem(1000, 3000)
    # dst_ip2 = RangeItem(1000, 1000)
    # vlan2 = SetItem([1, 2, 4])
    # port2 = DotItem(80)
    
    sw_3 = DotItem(3)
    sw_4 = DotItem(4)
    
    c_1 = Constraint(['fwd_port'], [1])
    c_2 = Constraint(['fwd_port'], [2])
    c_3 = Constraint(['fwd_port'], [3])
    
    a_1 = Annotation([('FORBID', 1),('TOWARDS', 2)])
    a_2 = Annotation([('FORBID', 2),('TOWARDS', 4)])
    a_3 = Annotation([('FORBID', 4),('FORWARD', 2)])
    
    a_4 = Annotation([('FORBID', 1),('TOWARDS', 3)])
    a_5 = Annotation([('FORBID', 3),('TOWARDS', 4)])
    a_6 = Annotation([('FORBID', 4),('FORWARD', 2)])
'''
    
    
from itertools import *    
from inst import *
from networks import *
from lisa_types import *
from util.utils import *
from ryu.lib import hub
import time

class Middle_End():

    def __init__(self):
      '''
      for lisa
      switch_dof: like this, [[sw1, port1, dof], [sw2, port2, dof] ...]
      full_path: a list contains the switch from sw1 to swn, like this, [sw1, sw2, sw3, ..., swn]
      '''
      self.names = ['switch', 'dst_ip']

      #      global multi_dof
      # multi_dof = []
      self.now_multi_dof = []
      self.collect_dof = hub.spawn(self._collect)
      self.f1 = open("controller_dof_1","r")
      self.f2 = open("controller_dof_2","r")


    # collet multi dof from all controllers
    def _collect(self):
      i = 0
      while True:
        self.eliminate_conflict()
        if i == 1:
          self.update_multi_dof()
          i = 0
        hub.sleep(10)
        i += 1

    # update the dof from controllers every 10ms
    def update_multi_dof(self):
      multi_dof = self.get_dof_from_files()
      self.now_multi_dof = multi_dof
      print self.now_multi_dof

    def get_dof_from_files(self):
      multi_dof = []
      dof_1 = ' '
      dof_2 = ' '
      self.f1 = open("controller_dof_1","r")
      self.f2 = open("controller_dof_2","r")
      f1_content = self.f1.readlines()
      f2_content = self.f2.readlines()
      if f1_content:
          # print f1_content
          # print f1_content[0]
          # print "self.f1.readlines()"
          # print self.f1.readlines()
          dof_1 = f1_content[0]
      if f2_content:
          # print self.f2.readlines()
          dof_2 = f2_content[0]
      c_dof_1 = eval(dof_1)
      self.f1.close()
      self.f2.close()
      if c_dof_1 not in multi_dof:
        multi_dof.append(c_dof_1)
      c_dof_2 = eval(dof_2)
      if c_dof_2 not in multi_dof:
        multi_dof.append(c_dof_2)
      print multi_dof
      return multi_dof


    # eliminate conflict every 10ms 
    def eliminate_conflict(self):
      instruction_sets, scope_sets = self.construct_instructions(self.now_multi_dof)    
      print '------------------------------instruction_sets----------------------------------'
      print instruction_sets
      for instru in instruction_sets:
        print instru.scope.scope_dict, instru.constraint.action_dict, instru.annotation.anno
      if self.instruction_conflict_test(instruction_sets):
        priority_dict = self.instruction_decouple_test(instruction_sets)
        print "--------------------------priority_dict---------------------------"
        for key, value in priority_dict.items():
          print key, value
          for inst in value:
            print key, inst.scope.scope_dict, inst.constraint.action_dict, inst.annotation.anno
        inst_sets = self.instruction_set_test(priority_dict)
        self.elimination_test(inst_sets)      


    def construct_instructions(self, now_multi_dof):
      instruction_sets = []
      scope_sets = []
      sw_sets = []
      for controller_dof in now_multi_dof:
        switch_dof, full_path = controller_dof[0], controller_dof[1]
        dst_ip_lower = ip2long(switch_dof[-1][-1].split(' ')[1]) 
        dst_ip_upper = ip2long(switch_dof[-1][-1].split(' ')[1]) 
        dst_ip = RangeItem(dst_ip_lower, dst_ip_upper)
        for switch in switch_dof:
          tmp_sw = DotItem(switch[0])
          if tmp_sw not in sw_sets:
            sw_sets.append(tmp_sw)
          tmp_scope = Scope(self.names, [tmp_sw, dst_ip])
          if tmp_scope not in scope_sets:
            scope_sets.append(tmp_scope)
          tmp_constraint = Constraint(['fwd_port'], [switch[1]])
          tmp_annotation = Annotation([('FORBID', switch[0]),(switch[-1].split(' ')[0], switch[-1].split(' ')[1])])
          tmp_instruction = Instruction(tmp_scope, tmp_constraint, tmp_annotation)
          if tmp_instruction not in instruction_sets:
            instruction_sets.append(tmp_instruction)
      return instruction_sets, scope_sets

    def scope_ovserlap_test(self, scope_set):
        flag = False
        print '################scope overlapping test################'
        '''
        scope1 = Scope(names, [sw_1, dst_ip])
        scope2 = Scope(names, [sw_2, dst_ip])
        scope3 = Scope(names, [sw_3, dst_ip])
        scope4 = Scope(names, [sw_4, dst_ip])
        scope1.dump()
        scope2.dump()
        if scope1.overlaps(scope2):
        conflicting_scope = scope1.decouples_scope(scope2)
        conflicting_scope.dump()
        '''
        for i in range(len(scope_set)):
          for j in range(i+1, len(scope_set)):
            if scope_set[i].overlaps(scope_set[j]):
              # conflicting_scope = scope_set[i].decouples_scope(scope_set[j])
              # conflicting_scope.dump()
              flag = True
              break
          if flag == True:
            break
        return flag


    def instruction_conflict_test(self, instruction_set):
        flag = False
        print '################instruction conflicting test################'
        '''
        # A DstIP 10.0.0.2 FORWARD 2
        inst_1 = Instruction(scope1, c_2, a_1)
        # B DstIP 10.0.0.2 FORWARD 3
        inst_2 = Instruction(scope2, c_3, a_2)
        # D DstIP 10.0.0.2 FORWARD 2
        inst_3 = Instruction(scope4, c_2, a_3)
        # A DstIP 10.0.0.2 FORWARD 3
        inst_4 = Instruction(scope1, c_3, a_4)
        # C DstIP 10.0.0.2 FORWARD 2
        inst_5 = Instruction(scope3, c_2, a_5)
        # D DstIP 10.0.0.2 FORWARD 2
        inst_6 = Instruction(scope4, c_2, a_6)    
        
        if inst_1.conflicts(inst_2):
          n_1, n_2 = inst_1.decouples(inst_2)
          n_1.dump()
          n_2.dump()
        '''
        for i in range(len(instruction_set)):
          for j in range(i+1, len(instruction_set)):
            if instruction_set[i].conflicts(instruction_set[j]):
              # n_1, n_2 = instruction_set[i].decouples(instruction_set[j])
              # n_1.dump()
              # n_2.dump()
              flag = True
              break
          if flag == True:
            break
        return flag

    def instruction_decouple_test(self, instruction_set):
        print '################instruction decouple test################'
        # raw_inst = [inst_1, inst_2, inst_3, inst_4, inst_5, inst_6]
        raw_inst = instruction_set
        priority_dict = {0: raw_inst}
        art_pri = 0
        while True:
          if art_pri not in priority_dict.keys():
            print 'no such inst set with priority %s' % str(art_pri)
            break
          else:
            for t in combinations(priority_dict[art_pri], 2):
              if t[0].conflicts(t[1]) and not t[0].scope == t[1].scope:
                n_1, n_2 = t[0].decouples(t[1])
                if art_pri+1 not in priority_dict.keys(): priority_dict[art_pri+1] = []
                priority_dict[art_pri+1].extend([n_1, n_2])
          art_pri += 1
        
        # NOTE: need to sort the inst in the dict to use the groupby function
        for k in priority_dict.keys():
          priority_dict[k].sort(key = lambda inst: inst.scope.get_attr('switch').items)
        
          print k,
          for inst in priority_dict[k]:
            inst.dump()

          return priority_dict

    def instruction_set_test(self, priority_dict):    
        print '################instruction set test################'
        
        inst_sets = []
        for p in priority_dict.keys():
          art_insts = priority_dict[p]
          for i, k in groupby(art_insts, lambda inst: inst.scope):
            art_set = InstSet(list(k), p)
            inst_sets.append(art_set)
            
            print 'the %s insts with the following scope:' % len(art_set.insts)
            i.dump()
            print 'insts:'
            for n in art_set.insts:
              n.dump()
            print 'end'
        
        for sid, inst_set in groupby(inst_sets, lambda set: set.get_scope().get_attr('switch').items):
          if sid not in switch_set_map.keys(): switch_set_map[sid] = []
          switch_set_map[sid].extend(inst_set)
        
        for sets in switch_set_map.values():
          sets.sort(reverse = True, key = lambda s: s.priority)

        return inst_sets
    
        
    def topology_test(self):
        print '################topology test################'
        s_a = Switch(1, 3)
        s_b = Switch(2, 3)
        s_c = Switch(3, 3)
        s_d = Switch(4, 3)
        
        for s in [s_a, s_b, s_c, s_d]:
          switches[s.sid] = s
        
        # assume double link graph
        add_double_link(s_a.ports[2], s_b.ports[1])
        add_double_link(s_a.ports[3], s_c.ports[1])
        add_double_link(s_b.ports[2], s_c.ports[3])
        add_double_link(s_b.ports[3], s_d.ports[1])
        add_double_link(s_c.ports[2], s_d.ports[3])
        
        # edge ports
        add_edge_ports(s_a.ports[1])
        add_edge_ports(s_d.ports[2])
        
        for s in switches.values():
          s.dump()

    def elimination_test(self, inst_sets):
        print '################elimination test################'
        
        for set in inst_sets:
          print set.size()
          if set.size() > 1:
            for instruction in set.insts:
                print instruction.scope.scope_dict, instruction.constraint.action_dict, instruction.annotation.anno
            print 'ready to eliminate'
            print set.eliminates()
            has_eliminated, path = set.eliminates()
            if has_eliminated:
              print 'successful elimination'
              print "the path is"
              print path
            else:
              print 'cannot eliminated'
        
        for set in inst_sets:
          inst = set.insts[0]
          inst.dump()
    
