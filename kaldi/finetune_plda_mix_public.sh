. ./cmd.sh
. ./path.sh
set -e
mfccdir=`pwd`/mfcc
vaddir=`pwd`/mfcc

voting_root=/data/greyheron/not-backed-up/aims/aimsre/xxlu/audio_scan/revision/50vs20_PLM_soft_scan_100/final_result/voting
nnet_dir=0007_voxceleb_v2_1a/exp/xvector_nnet_1a
orig_plda_data_dir=../v2/data/plda_v1
new_plda_dir=exp/mix_plda_50vs20_PLM_soft_scan_100

. utils/parse_options.sh

###combine associated data with the original PLDA training data
rm -rf data/mix_50vs20_PLM_soft_scan_100
utils/combine_data.sh data/mix_50vs20_PLM_soft_scan_100 $orig_plda_data_dir data/50vs20_PLM_soft_scan_100_voting

# Make MFCCs and compute the energy-based VAD for each dataset
steps/make_mfcc.sh --write-utt2num-frames true --mfcc-config conf/mfcc.conf --nj 80 --cmd "$train_cmd" \
    data/mix_50vs20_PLM_soft_scan_100 exp/make_mfcc $mfccdir
utils/fix_data_dir.sh data/mix_50vs20_PLM_soft_scan_100

sid/compute_vad_decision.sh --nj 80 --cmd "$train_cmd" \
    data/mix_50vs20_PLM_soft_scan_100 exp/make_vad $vaddir
utils/fix_data_dir.sh data/mix_50vs20_PLM_soft_scan_100


sid/nnet3/xvector/extract_xvectors.sh --cmd "$train_cmd --mem 4G" --nj 80 \
  $nnet_dir data/mix_50vs20_PLM_soft_scan_100 \
  $new_plda_dir


# update mean
$train_cmd $new_plda_dir/log/compute_mean.log \
  ivector-mean scp:$new_plda_dir/xvector.scp \
  $new_plda_dir/mean.vec || exit 1;

# update PLDA model
lda_dim=200
$train_cmd $new_plda_dir/log/lda.log \
  ivector-compute-lda --total-covariance-factor=0.0 --dim=$lda_dim \
  "ark:ivector-subtract-global-mean scp:$new_plda_dir/xvector.scp ark:- |" \
  ark:data/mix_50vs20_PLM_soft_scan_100/utt2spk $new_plda_dir/transform.mat || exit 1;

$train_cmd $new_plda_dir/log/plda.log \
  ivector-compute-plda ark:data/mix_50vs20_PLM_soft_scan_100/spk2utt \
  "ark:ivector-subtract-global-mean scp:$new_plda_dir/xvector.scp ark:- | transform-vec $new_plda_dir/transform.mat ark:- ark:- | ivector-normalize-length ark:-  ark:- |" \
  $new_plda_dir/plda || exit 1;
