from __future__ import annotations
import heapq, itertools
from dataclasses import dataclass

def grid_to_tuple(grid):
    return tuple(tuple(r) for r in grid)

def tuple_to_grid(t):
    return [list(r) for r in t]

def apply_grid(futo, grid):
    futo.grid = [r[:] for r in grid]

def h_zero(futo, grid): return 0

def h_rc(futo, grid):
    row_zeros = [sum(v==0 for v in row) for row in grid]
    col_zeros = [sum(grid[r][c]==0 for r in range(futo.N)) for c in range(futo.N)]
    return max(max(row_zeros, default=0), max(col_zeros, default=0))
HEURISTICS={'h0':h_zero,'hrc':h_rc}

def is_value_consistent(futo, grid, row, col, val):
    n=futo.N
    for j in range(n):
        if j!=col and grid[row][j]==val: return False
    for i in range(n):
        if i!=row and grid[i][col]==val: return False
    if col>0:
        left=grid[row][col-1]; rel=futo.h_constraints[row][col-1]
        if left!=0:
            if rel==1 and not(left<val): return False
            if rel==-1 and not(left>val): return False
    if col<n-1:
        right=grid[row][col+1]; rel=futo.h_constraints[row][col]
        if right!=0:
            if rel==1 and not(val<right): return False
            if rel==-1 and not(val>right): return False
    if row>0:
        up=grid[row-1][col]; rel=futo.v_constraints[row-1][col]
        if up!=0:
            if rel==1 and not(up<val): return False
            if rel==-1 and not(up>val): return False
    if row<n-1:
        down=grid[row+1][col]; rel=futo.v_constraints[row][col]
        if down!=0:
            if rel==1 and not(val<down): return False
            if rel==-1 and not(val>down): return False
    return True

def get_candidates(futo, grid, row, col):
    cur=grid[row][col]
    if cur!=0:
        return [cur] if is_value_consistent(futo, grid, row, col, cur) else []
    return [v for v in range(1,futo.N+1) if is_value_consistent(futo,grid,row,col,v)]

def propagate_constraints(futo, grid):
    n=futo.N
    assignments=0
    while True:
        changed=False
        candidates_map={}
        for i in range(n):
            for j in range(n):
                if grid[i][j]!=0: continue
                cand=get_candidates(futo, grid, i, j)
                if not cand: return None, None
                candidates_map[(i,j)] = cand
                if len(cand)==1:
                    grid[i][j]=cand[0]
                    assignments += 1
                    changed=True
        if changed:
            continue
        for i in range(n):
            empties=[(i,j) for j in range(n) if grid[i][j]==0]
            if not empties: continue
            for val in range(1,n+1):
                spots=[pos for pos in empties if val in candidates_map[pos]]
                if len(spots)==1:
                    r,c=spots[0]
                    grid[r][c]=val
                    assignments += 1
                    changed=True
                    break
            if changed: break
        if changed:
            continue
        for j in range(n):
            empties=[(i,j) for i in range(n) if grid[i][j]==0]
            if not empties: continue
            for val in range(1,n+1):
                spots=[pos for pos in empties if val in candidates_map[pos]]
                if len(spots)==1:
                    r,c=spots[0]
                    grid[r][c]=val
                    assignments += 1
                    changed=True
                    break
            if changed: break
        if not changed:
            return grid, assignments

def select_unassigned_cell_mrv(futo, grid):
    best=None; best_size=None; best_degree=-1
    n=futo.N
    for i in range(n):
        for j in range(n):
            if grid[i][j]!=0: continue
            size=len(get_candidates(futo,grid,i,j))
            degree=sum(grid[i][jj]==0 for jj in range(n) if jj!=j)+sum(grid[ii][j]==0 for ii in range(n) if ii!=i)
            if j>0 and grid[i][j-1]==0: degree+=1
            if j<n-1 and grid[i][j+1]==0: degree+=1
            if i>0 and grid[i-1][j]==0: degree+=1
            if i<n-1 and grid[i+1][j]==0: degree+=1
            if best_size is None or size<best_size or (size==best_size and degree>best_degree):
                best=(i,j); best_size=size; best_degree=degree
    return best

def affected_cells(futo,row,col):
    seen={(row,col)}
    for j in range(futo.N): seen.add((row,j))
    for i in range(futo.N): seen.add((i,col))
    if col>0: seen.add((row,col-1))
    if col<futo.N-1: seen.add((row,col+1))
    if row>0: seen.add((row-1,col))
    if row<futo.N-1: seen.add((row+1,col))
    return seen

def order_values_lcv(futo, grid, row, col):
    candidates=get_candidates(futo, grid, row, col)
    if len(candidates)<=1: return candidates
    impacted=[(i,j) for i,j in affected_cells(futo,row,col) if (i,j)!=(row,col) and grid[i][j]==0]
    scored=[]
    for val in candidates:
        grid[row][col]=val
        score=0
        for i,j in impacted:
            score += len(get_candidates(futo,grid,i,j))
        grid[row][col]=0
        scored.append((score,val))
    scored.sort(reverse=True)
    return [v for _,v in scored]

def is_complete_and_valid(futo, grid):
    n=futo.N; target=set(range(1,n+1))
    for row in grid:
        if 0 in row or set(row)!=target: return False
    for c in range(n):
        if {grid[r][c] for r in range(n)} != target: return False
    for r in range(n):
        for c in range(n-1):
            rel=futo.h_constraints[r][c]; a,b=grid[r][c],grid[r][c+1]
            if rel==1 and not(a<b): return False
            if rel==-1 and not(a>b): return False
    for r in range(n-1):
        for c in range(n):
            rel=futo.v_constraints[r][c]; a,b=grid[r][c],grid[r+1][c]
            if rel==1 and not(a<b): return False
            if rel==-1 and not(a>b): return False
    return True
@dataclass(frozen=True)
class Node:
    grid_t: tuple
    g: int
    h: int
    @property
    def f(self): return self.g+self.h

def solve_futoshiki_astar(futo, heuristic_name='hrc'):
    heuristic_fn=HEURISTICS[heuristic_name]
    start_grid=[row[:] for row in futo.grid]
    start_grid, _ = propagate_constraints(futo,start_grid)
    if start_grid is None: return False, {'expansions':1,'generated':0,'heuristic':heuristic_name}
    start_t=grid_to_tuple(start_grid)
    start_g=sum(v!=0 for row in start_grid for v in row)
    start_node=Node(start_t,start_g,heuristic_fn(futo,start_grid))
    open_heap=[]; counter=itertools.count(); best_g={start_t:start_g}
    heapq.heappush(open_heap,(start_node.f,start_node.h,-start_g,next(counter),start_node))
    stats={'expansions':0,'generated':0,'heuristic':heuristic_name}
    while open_heap:
        _,_,_,_,cur=heapq.heappop(open_heap)
        if best_g.get(cur.grid_t)!=cur.g: continue
        grid=tuple_to_grid(cur.grid_t)
        stats['expansions'] += 1
        if is_complete_and_valid(futo,grid): apply_grid(futo,grid); return True, stats
        cell=select_unassigned_cell_mrv(futo,grid)
        if cell is None: continue
        r,c=cell
        values=order_values_lcv(futo,grid,r,c)
        stats['generated'] += len(values)
        for val in values:
            child=[row[:] for row in grid]
            child[r][c]=val
            child, _ = propagate_constraints(futo, child)
            if child is None: continue
            child_t=grid_to_tuple(child)
            new_g=sum(v!=0 for row in child for v in row)
            old=best_g.get(child_t)
            if old is not None and new_g>=old: continue
            child_h=heuristic_fn(futo,child)
            best_g[child_t]=new_g
            heapq.heappush(open_heap,(new_g+child_h,child_h,-new_g,next(counter),Node(child_t,new_g,child_h)))
    return False, stats
