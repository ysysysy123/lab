#!/usr/bin/env python3
"""
ik_2d_toy.py — 零第三方依赖！60 行纯标准库跑通平面二连杆机械臂正运动学 (FK) 与阻尼最小二乘逆运动学 (DLS-IK)
运行验证: python3 projects/p4-robot-learning/src/ik_2d_toy.py

W11 学习目标:
  看懂 2x2 雅可比矩阵 J = ∂(x,y)/∂(q1,q2) 如何把「关节角速度」映射为「末端线速度」，
  以及阻尼项 λ²I 如何防止机械臂伸直（奇异位形）时求逆爆炸！搞懂这个再去写 MuJoCo 7自由度 Franka IK 易如反掌。
"""

from __future__ import annotations

import math

L1, L2 = 1.0, 0.8  # 两节连杆长度 (m)


def forward_kinematics(q1: float, q2: float) -> tuple[float, float]:
    """已知关节角 (q1, q2) 求末端坐标 (x, y)"""
    x = L1 * math.cos(q1) + L2 * math.cos(q1 + q2)
    y = L1 * math.sin(q1) + L2 * math.sin(q1 + q2)
    return x, y


def jacobian(q1: float, q2: float) -> tuple[tuple[float, float], tuple[float, float]]:
    """末端位置对 (q1, q2) 的 2x2 偏导矩阵 J"""
    j11 = -L1 * math.sin(q1) - L2 * math.sin(q1 + q2)
    j12 = -L2 * math.sin(q1 + q2)
    j21 = L1 * math.cos(q1) + L2 * math.cos(q1 + q2)
    j22 = L2 * math.cos(q1 + q2)
    return (j11, j12), (j21, j22)


def solve_ik_dls(
    target_xy: tuple[float, float],
    init_q: tuple[float, float] = (0.2, 0.5),
    damping: float = 0.05,
    step_scale: float = 0.6,
    max_iters: int = 100,
    tol: float = 1e-4,
) -> tuple[float, float, int]:
    """阻尼最小二乘逆运动学: Δq = J^T (J J^T + λ² I)^(-1) e"""
    q1, q2 = init_q
    tx, ty = target_xy
    lam2 = damping * damping

    for it in range(1, max_iters + 1):
        cx, cy = forward_kinematics(q1, q2)
        ex, ey = tx - cx, ty - cy
        err = math.hypot(ex, ey)
        if err < tol:
            return q1, q2, it

        (j11, j12), (j21, j22) = jacobian(q1, q2)
        # 计算 M = J * J^T + λ² I (2x2 对称正定矩阵)
        m11 = j11 * j11 + j12 * j12 + lam2
        m12 = j11 * j21 + j12 * j22
        m22 = j21 * j21 + j22 * j22 + lam2
        det = m11 * m22 - m12 * m12

        # u = M^(-1) * e
        ux = (m22 * ex - m12 * ey) / det
        uy = (-m12 * ex + m11 * ey) / det

        # Δq = J^T * u
        dq1 = j11 * ux + j21 * uy
        dq2 = j12 * ux + j22 * uy
        q1 += step_scale * dq1
        q2 += step_scale * dq2

    raise RuntimeError("IK 未在限定步数内收敛（请检查目标点是否超出工作空间半径 L1+L2）")


if __name__ == "__main__":
    goal = (0.9, 1.1)  # 位于最大臂展 1.8m 以内
    q1_sol, q2_sol, steps = solve_ik_dls(goal)
    rx, ry = forward_kinematics(q1_sol, q2_sol)
    final_err = math.hypot(goal[0] - rx, goal[1] - ry)

    assert final_err < 1e-4
    print(f"✅ 2D 阻尼伪逆 IK 收敛！用时 {steps} 步")
    print(f"   目标坐标: {goal} → 实际到达: ({rx:.5f}, {ry:.5f}), 误差: {final_err:.2e} m")
    print(f"   求得关节角: q1 = {math.degrees(q1_sol):.2f}°, q2 = {math.degrees(q2_sol):.2f}°")

