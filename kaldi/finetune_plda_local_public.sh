. ./cmd.sh
. ./path.sh
set -e
mfccdir=`pwd`/mfcc
vaddir=`pwd`/mfcc

voting_root=/data/greyheron/not-backed-up/aims/aimsre/xxlu/audio_scan/revision/50vs20_PLM_soft_scan_100/final_result/voting
nnet_dir=0007_voxceleb_v2_1a/exp/xvector_nnet_1a
orig_plda_data_dir=../v2/data/plda_v1
new_plda_dir=exp/local_plda_50vs20_PLM_soft_scan_100

. utils/parse_options.sh

rm -rf data/50vs20_PLM_soft_scan_100_voting
local/make_synth_voting.pl $voting_root data/50vs20_PLM_soft_scan_100_voting


# Make MFCCs and compute the energy-based VAD for each dataset
steps/make_mfcc.sh --write-utt2num-frames true --mfcc-config conf/mfcc.conf --nj 10 --cmd "$train_cmd" \
    data/50vs20_PLM_soft_scan_100_voting exp/make_mfcc $mfccdir
utils/fix_data_dir.sh data/50vs20_PLM_soft_scan_100_voting

sid/compute_vad_decision.sh --nj 10 --cmd "$train_cmd" \
    data/50vs20_PLM_soft_scan_100_voting exp/make_vad $vaddir
utils/fix_data_dir.sh data/50vs20_PLM_soft_scan_100_voting


sid/nnet3/xvector/extract_xvectors.sh --cmd "$train_cmd --mem 4G" --nj 30 \
  $nnet_dir data/50vs20_PLM_soft_scan_100_voting \
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
  ark:data/50vs20_PLM_soft_scan_100_voting/utt2spk $new_plda_dir/transform.mat || exit 1;

$train_cmd $new_plda_dir/log/plda.log \
  ivector-compute-plda ark:data/50vs20_PLM_soft_scan_100_voting/spk2utt \
  "ark:ivector-subtract-global-mean scp:$new_plda_dir/xvector.scp ark:- | transform-vec $new_plda_dir/transform.mat ark:- ark:- | ivector-normalize-length ark:-  ark:- |" \
  $new_plda_dir/plda || exit 1;
