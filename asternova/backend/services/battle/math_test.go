package battle

import (
	"math"
	"testing"
)

func almostEqual(a, b float64) bool {
	const eps = 1e-9
	return math.Abs(a-b) <= eps*(1+math.Abs(a)+math.Abs(b))
}

func vectorsAlmostEqual(a, b Vector2) bool {
	return almostEqual(a.X, b.X) && almostEqual(a.Z, b.Z)
}

func TestVector2Add(t *testing.T) {
	cases := []struct {
		name string
		v, o Vector2
		want Vector2
	}{
		{"正数相加", Vector2{1, 2}, Vector2{3, 4}, Vector2{4, 6}},
		{"含负数", Vector2{-1, 5}, Vector2{1, -5}, Vector2{0, 0}},
		{"零向量", Vector2{0, 0}, Vector2{7, 8}, Vector2{7, 8}},
	}
	for _, tc := range cases {
		t.Run(tc.name, func(t *testing.T) {
			got := tc.v.Add(tc.o)
			if !vectorsAlmostEqual(got, tc.want) {
				t.Errorf("Add(%v, %v) = %v, want %v", tc.v, tc.o, got, tc.want)
			}
		})
	}
}

func TestVector2Sub(t *testing.T) {
	cases := []struct {
		name string
		v, o Vector2
		want Vector2
	}{
		{"正数相减", Vector2{5, 7}, Vector2{2, 3}, Vector2{3, 4}},
		{"结果为负", Vector2{1, 1}, Vector2{2, 3}, Vector2{-1, -2}},
		{"自身相减为零", Vector2{9, 9}, Vector2{9, 9}, Vector2{0, 0}},
	}
	for _, tc := range cases {
		t.Run(tc.name, func(t *testing.T) {
			got := tc.v.Sub(tc.o)
			if !vectorsAlmostEqual(got, tc.want) {
				t.Errorf("Sub(%v, %v) = %v, want %v", tc.v, tc.o, got, tc.want)
			}
		})
	}
}

func TestVector2Mul(t *testing.T) {
	cases := []struct {
		name   string
		v      Vector2
		scalar float64
		want   Vector2
	}{
		{"正标量", Vector2{3, -4}, 2, Vector2{6, -8}},
		{"零标量归零", Vector2{3, 4}, 0, Vector2{0, 0}},
		{"负标量反向", Vector2{1, 2}, -1, Vector2{-1, -2}},
		{"小数标量", Vector2{10, 20}, 0.5, Vector2{5, 10}},
	}
	for _, tc := range cases {
		t.Run(tc.name, func(t *testing.T) {
			got := tc.v.Mul(tc.scalar)
			if !vectorsAlmostEqual(got, tc.want) {
				t.Errorf("Mul(%v, %v) = %v, want %v", tc.v, tc.scalar, got, tc.want)
			}
		})
	}
}

func TestVector2Length(t *testing.T) {
	cases := []struct {
		name string
		v    Vector2
		want float64
	}{
		{"3-4-5 直角三角形", Vector2{3, 4}, 5},
		{"零向量长度为零", Vector2{0, 0}, 0},
		{"纯 X 轴", Vector2{-7, 0}, 7},
		{"纯 Z 轴", Vector2{0, -1.5}, 1.5},
	}
	for _, tc := range cases {
		t.Run(tc.name, func(t *testing.T) {
			got := tc.v.Length()
			if !almostEqual(got, tc.want) {
				t.Errorf("Length(%v) = %v, want %v", tc.v, got, tc.want)
			}
		})
	}
}

func TestVector2Normalized(t *testing.T) {
	cases := []struct {
		name string
		v    Vector2
		want Vector2
	}{
		{"常规归一化", Vector2{3, 4}, Vector2{0.6, 0.8}},
		{"零向量返回零向量", Vector2{0, 0}, Vector2{0, 0}},
		{"单位向量不变", Vector2{1, 0}, Vector2{1, 0}},
		{"负方向归一化", Vector2{0, -5}, Vector2{0, -1}},
	}
	for _, tc := range cases {
		t.Run(tc.name, func(t *testing.T) {
			got := tc.v.Normalized()
			if !vectorsAlmostEqual(got, tc.want) {
				t.Errorf("Normalized(%v) = %v, want %v", tc.v, got, tc.want)
			}
		})
	}
}

func TestVector2Dot(t *testing.T) {
	cases := []struct {
		name string
		v, o Vector2
		want float64
	}{
		{"常规点积", Vector2{1, 2}, Vector2{3, 4}, 11},
		{"垂直点积为零", Vector2{1, 0}, Vector2{0, 1}, 0},
		{"反向点积为负", Vector2{1, 0}, Vector2{-2, 0}, -2},
	}
	for _, tc := range cases {
		t.Run(tc.name, func(t *testing.T) {
			got := tc.v.Dot(tc.o)
			if !almostEqual(got, tc.want) {
				t.Errorf("Dot(%v, %v) = %v, want %v", tc.v, tc.o, got, tc.want)
			}
		})
	}
}

func TestVector2Lerp(t *testing.T) {
	cases := []struct {
		name   string
		v, tgt Vector2
		weight float64
		want   Vector2
	}{
		{"weight 0 返回自身", Vector2{1, 1}, Vector2{5, 9}, 0, Vector2{1, 1}},
		{"weight 0.5 取中点", Vector2{0, 0}, Vector2{10, 20}, 0.5, Vector2{5, 10}},
		{"weight 1 到达目标", Vector2{1, 2}, Vector2{5, 9}, 1, Vector2{5, 9}},
	}
	for _, tc := range cases {
		t.Run(tc.name, func(t *testing.T) {
			got := tc.v.Lerp(tc.tgt, tc.weight)
			if !vectorsAlmostEqual(got, tc.want) {
				t.Errorf("Lerp(%v -> %v, %v) = %v, want %v", tc.v, tc.tgt, tc.weight, got, tc.want)
			}
		})
	}
}

func TestVector2MoveToward(t *testing.T) {
	cases := []struct {
		name     string
		v, tgt   Vector2
		maxDelta float64
		want     Vector2
	}{
		{"余量充足直接到达", Vector2{0, 0}, Vector2{3, 4}, 10, Vector2{3, 4}},
		{"余量不足按比例推进", Vector2{0, 0}, Vector2{3, 4}, 2.5, Vector2{1.5, 2}},
		{"maxDelta 为零原地不动", Vector2{0, 0}, Vector2{3, 4}, 0, Vector2{0, 0}},
		{"已在目标点返回目标", Vector2{3, 4}, Vector2{3, 4}, 1, Vector2{3, 4}},
	}
	for _, tc := range cases {
		t.Run(tc.name, func(t *testing.T) {
			got := tc.v.MoveToward(tc.tgt, tc.maxDelta)
			if !vectorsAlmostEqual(got, tc.want) {
				t.Errorf("MoveToward(%v -> %v, %v) = %v, want %v", tc.v, tc.tgt, tc.maxDelta, got, tc.want)
			}
		})
	}
}
