; ModuleID = 'literal-view.c'
source_filename = "literal-view.c"
target datalayout = "e-m:e-p:32:32-p10:8:8-p20:8:8-i64:64-i128:128-n32:64-S128-ni:1:10:20"
target triple = "wasm32"

@buffer = internal global [16384 x i8] zeroinitializer, align 16

; Function Attrs: mustprogress nofree norecurse nosync nounwind willreturn memory(none)
define hidden noundef nonnull ptr @pixels() local_unnamed_addr #0 {
  ret ptr @buffer
}

; Function Attrs: mustprogress nofree norecurse nosync nounwind willreturn memory(none)
define hidden noundef i32 @capacity() local_unnamed_addr #0 {
  ret i32 16384
}

; Function Attrs: nofree norecurse nosync nounwind memory(write, argmem: none, inaccessiblemem: none)
define hidden range(i32 0, 12289) i32 @render(i32 noundef %0) local_unnamed_addr #1 {
  %2 = icmp eq i32 %0, 256
  br i1 %2, label %3, label %32

3:                                                ; preds = %1, %29
  %4 = phi i32 [ %30, %29 ], [ 0, %1 ]
  %5 = shl nuw nsw i32 %4, 8
  br label %6

6:                                                ; preds = %6, %3
  %7 = phi i32 [ 0, %3 ], [ %27, %6 ]
  %8 = shl nuw nsw i32 %7, 2
  %9 = add nuw nsw i32 %8, %5
  %10 = getelementptr inbounds nuw [16384 x i8], ptr @buffer, i32 0, i32 %9
  store i8 96, ptr %10, align 8, !tbaa !2
  %11 = or disjoint i32 %9, 1
  %12 = getelementptr inbounds nuw [16384 x i8], ptr @buffer, i32 0, i32 %11
  store i8 64, ptr %12, align 1, !tbaa !2
  %13 = or disjoint i32 %9, 2
  %14 = getelementptr inbounds nuw [16384 x i8], ptr @buffer, i32 0, i32 %13
  store i8 95, ptr %14, align 2, !tbaa !2
  %15 = or disjoint i32 %9, 3
  %16 = getelementptr inbounds nuw [16384 x i8], ptr @buffer, i32 0, i32 %15
  store i8 -1, ptr %16, align 1, !tbaa !2
  %17 = shl i32 %7, 2
  %18 = or disjoint i32 %17, 4
  %19 = add nuw nsw i32 %18, %5
  %20 = getelementptr inbounds nuw [16384 x i8], ptr @buffer, i32 0, i32 %19
  store i8 96, ptr %20, align 4, !tbaa !2
  %21 = or disjoint i32 %19, 1
  %22 = getelementptr inbounds nuw [16384 x i8], ptr @buffer, i32 0, i32 %21
  store i8 64, ptr %22, align 1, !tbaa !2
  %23 = or disjoint i32 %19, 2
  %24 = getelementptr inbounds nuw [16384 x i8], ptr @buffer, i32 0, i32 %23
  store i8 95, ptr %24, align 2, !tbaa !2
  %25 = or disjoint i32 %19, 3
  %26 = getelementptr inbounds nuw [16384 x i8], ptr @buffer, i32 0, i32 %25
  store i8 -1, ptr %26, align 1, !tbaa !2
  %27 = add nuw nsw i32 %7, 2
  %28 = icmp eq i32 %27, 64
  br i1 %28, label %29, label %6, !llvm.loop !5

29:                                               ; preds = %6
  %30 = add nuw nsw i32 %4, 1
  %31 = icmp eq i32 %30, 48
  br i1 %31, label %32, label %3, !llvm.loop !7

32:                                               ; preds = %29, %1
  %33 = phi i32 [ 0, %1 ], [ 12288, %29 ]
  ret i32 %33
}

attributes #0 = { mustprogress nofree norecurse nosync nounwind willreturn memory(none) "no-builtins" "no-trapping-math"="true" "stack-protector-buffer-size"="8" "target-cpu"="generic" "target-features"="+bulk-memory,+bulk-memory-opt,+call-indirect-overlong,+multivalue,+mutable-globals,+nontrapping-fptoint,+reference-types,+sign-ext" }
attributes #1 = { nofree norecurse nosync nounwind memory(write, argmem: none, inaccessiblemem: none) "no-builtins" "no-trapping-math"="true" "stack-protector-buffer-size"="8" "target-cpu"="generic" "target-features"="+bulk-memory,+bulk-memory-opt,+call-indirect-overlong,+multivalue,+mutable-globals,+nontrapping-fptoint,+reference-types,+sign-ext" }

!llvm.module.flags = !{!0}
!llvm.ident = !{!1}

!0 = !{i32 1, !"wchar_size", i32 4}
!1 = !{!"Apple clang version 21.0.0 (https://github.com/swiftlang/llvm-project.git b6f042d4515f83404d3f44012144b5e67b2c5791)"}
!2 = !{!3, !3, i64 0}
!3 = !{!"omnipotent char", !4, i64 0}
!4 = !{!"Simple C/C++ TBAA"}
!5 = distinct !{!5, !6}
!6 = !{!"llvm.loop.mustprogress"}
!7 = distinct !{!7, !6}
